#!/usr/bin/env python3
# coding: utf-8
"""ENTRE AMIGOS • V1: editor por manifesto para Windows + FFmpeg.
As 33 cenas são descritas em projeto_v1.json. Não cria depoimentos ou legendas.
Os cortes sem tempo final conhecido são provisórios; revisar antes da publicação.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unicodedata

BASE = Path(__file__).resolve().parent
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mpeg"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
AUDIO_EXT = {".m4a", ".mp3", ".wav", ".flac", ".aac"}
BANNED = {"1000434736.mp4"}
PIPELINE_VERSION = "2026-11-11-v2-safe-cache"

def fingerprint(*parts):
    """Signature for an output, including the complete edit recipe and source stats."""
    packed = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()

def source_stamp(path):
    path = Path(path).resolve()
    stat = path.stat()
    return [str(path), stat.st_size, stat.st_mtime_ns]

def cache_marker(path):
    return path.with_name(path.name + ".sha256")

def cache_ready(path, signature, expected=None):
    """Never reuse an output without matching recipe and valid A/V streams."""
    marker = cache_marker(path)
    if not path.exists() or path.stat().st_size < 16000 or not marker.exists():
        return False
    if marker.read_text(encoding="utf-8").strip() != signature:
        return False
    try:
        duration, streams = probe(path)
        return (duration > 0 and (expected is None or abs(duration - expected) < .7)
                and any(s.get("codec_type") == "video" for s in streams)
                and any(s.get("codec_type") == "audio" for s in streams))
    except Exception:
        return False

def stamp_cache(path, signature):
    cache_marker(path).write_text(signature, encoding="utf-8")

def validate_manifest(project):
    scenes = project.get("cenas", [])
    ids = [f"C{i:02d}" for i in range(1, 34)]
    if [s.get("id") for s in scenes] != ids:
        raise ValueError("Manifesto deve conter C01 a C33 em ordem, sem repetições")
    modes = {"bloco01", "bloco02", "dentro_bloco01", "dentro_bloco02",
             "montar", "creditos"}
    if [s["modo"] for s in scenes].count("bloco01") != 1:
        raise ValueError("O Bloco 01 deve ser incluído uma única vez")
    if [s["modo"] for s in scenes].count("bloco02") != 1:
        raise ValueError("O Bloco 02 deve ser incluído uma única vez")
    if scenes[0]["modo"] != "bloco01" or scenes[8]["modo"] != "bloco02":
        raise ValueError("Blocos não correspondem às cenas C01 e C09")
    if [s["modo"] for s in scenes[1:8]] != ["dentro_bloco01"] * 7:
        raise ValueError("C02 a C08 já estão dentro do Bloco 01")
    for scene in scenes:
        if scene.get("modo") not in modes:
            raise ValueError(f"Modo de edição inválido em {scene['id']}")
        for c in scene.get("clipes", []):
            if "arquivo" not in c or c["arquivo"].lower() in BANNED:
                raise ValueError(f"Arquivo sem nome ou excluído em {scene['id']}")
            if c.get("entrada") is not None and float(c["entrada"]) < 0:
                raise ValueError(f"Entrada negativa em {scene['id']}")
            if c.get("saida") is not None and float(c["saida"]) <= float(c.get("entrada") or 0):
                raise ValueError(f"Corte invertido em {scene['id']}")
            if c.get("audio", "mute") not in ("original", "mute"):
                raise ValueError(f"Tipo de áudio inválido em {scene['id']}")
    return True

def canon(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

def cmd(args, info=""):
    print("  >", info or str(args[0]), flush=True)
    result = subprocess.run([str(a) for a in args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, errors="replace")
    if result.returncode:
        raise RuntimeError((info + "\n" + result.stderr[-2500:]).strip())
    return result.stdout

def probe(file):
    value = json.loads(cmd(["ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height,r_frame_rate",
        "-of", "json", file], "Conferir formato"))
    return float(value.get("format", {}).get("duration") or 0), value.get("streams", [])

def index_files(root, extras):
    folder = Path(root).expanduser().resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Pasta de mídias não encontrada: {folder}")
    files = {}
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXT | IMAGE_EXT | AUDIO_EXT:
            continue
        if path.name.lower() in BANNED or "01 - abertura coletiva" in canon(str(path.parent)):
            continue
        files.setdefault(canon(path.name), path)
    for path in sorted(Path(extras).rglob("*")):
        if path.is_file() and path.suffix.lower() in VIDEO_EXT | IMAGE_EXT | AUDIO_EXT:
            files[canon(path.name)] = path
    return files

def asset(idx, name):
    # Os arquivos brutos podem chegar como .mp4.mpeg em alguns downloads.
    return idx.get(canon(name)) or idx.get(canon(name + ".mpeg"))

def music_asset(idx, aliases):
    tracks = [(k, v) for k, v in idx.items() if v.suffix.lower() in AUDIO_EXT]
    for term in aliases:
        for key, file in tracks:
            if canon(term) in key:
                return file
    return None

def get_image_png(source, cache):
    cache.mkdir(parents=True, exist_ok=True)
    signature = hashlib.sha1((str(source) + str(source.stat().st_size)).encode()).hexdigest()[:14]
    output = cache / (signature + ".png")
    if output.is_file():
        return output
    try:
        from PIL import Image, ImageOps
        if source.suffix.lower() in {".heic", ".heif"}:
            import pillow_heif
            pillow_heif.register_heif_opener()
    except ImportError as e:
        raise RuntimeError("Instale dependências: py -3 -m pip install -r requirements.txt") from e
    with Image.open(source) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.save(output, "PNG")
    return output

def duration_of(clip, source, cache):
    if source.suffix.lower() in IMAGE_EXT:
        return 0.0, float(clip.get("limite") or 4)
    length, streams = probe(source)
    start = float(clip.get("entrada") or 0)
    if clip.get("saida") is not None:
        available = float(clip["saida"]) - start
    else:
        available = float(clip.get("limite") or 12)
    return start, max(0, min(available, length - start - 0.12))

def render_clip(src, clip, out, image_cache):
    start, dur = duration_of(clip, src, image_cache)
    if dur < .45:
        raise ValueError(f"Trecho muito curto ou fora do arquivo: {src.name}, {start:.3f}s")
    recipe = fingerprint(PIPELINE_VERSION, "clip", source_stamp(src),
                         clip, round(start, 4), round(dur, 4), 1920, 1080, 24)
    if cache_ready(out, recipe, dur):
        print(f"  REUTILIZAR trecho: {out.name}", flush=True)
        return dur
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_name(out.stem + "_PARCIAL.mp4")
    vf = ("fps=24,scale=1920:1080:force_original_aspect_ratio=decrease,"
          "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p")
    if src.suffix.lower() in IMAGE_EXT:
        image = get_image_png(src, image_cache)
        inp = ["-loop", "1", "-framerate", "24", "-i", image,
               "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
        sound = ["-map", "0:v:0", "-map", "1:a:0"]
    else:
        _, streams = probe(src)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        inp = ["-ss", f"{start:.4f}", "-i", src]
        if has_audio:
            volume = "1.0" if clip.get("audio") == "original" else "0.0"
            sound = ["-map", "0:v:0", "-map", "0:a:0",
                     "-af", f"aresample=async=1:first_pts=0,volume={volume},apad"]
        else:
            inp += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
            sound = ["-map", "0:v:0", "-map", "1:a:0"]
    run = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y"] + inp + sound + [
        "-vf", vf, "-t", f"{dur:.4f}", "-r", "24",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-g", "48",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-ar", "48000", "-ac", "2", "-movflags", "+faststart", temp]
    try:
        cmd(run, f"Codificar {src.name}: {start:.2f}s + {dur:.2f}s")
        result_seconds, streams = probe(temp)
        if (abs(result_seconds - dur) > .7 or
                not any(v.get("codec_type") == "audio" for v in streams)):
            raise RuntimeError(f"Trecho não validado: {src.name}")
        os.replace(temp, out)
        stamp_cache(out, recipe)
    finally:
        if temp.exists():
            temp.unlink()
    return dur

def concat_list(paths, filename):
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w", encoding="utf-8") as f:
        for path in paths:
            fullname = str(path.resolve()).replace("\\", "/")
            fullname = fullname.replace("'", "'\\''")
            f.write(f"file '{fullname}'\n")

def concat_copy(paths, output):
    if not paths:
        raise ValueError("Lista vazia de segmentos")
    output.parent.mkdir(parents=True, exist_ok=True)
    expected = sum(probe(p)[0] for p in paths)
    recipe = fingerprint(PIPELINE_VERSION, "concat",
                         [source_stamp(p) for p in paths])
    if cache_ready(output, recipe, expected):
        print(f"  REUTILIZAR junção: {output.name}", flush=True)
        return
    tmp = output.with_name(output.stem + "_PARCIAL.mp4")
    try:
        if len(paths) == 1:
            shutil.copyfile(paths[0], tmp)
        else:
            lst = output.with_suffix(".concat.txt")
            concat_list(paths, lst)
            cmd(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y",
                 "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                 "-movflags", "+faststart", tmp], f"Juntar {len(paths)} tomadas")
        got, streams = probe(tmp)
        # Some compressed audio frames introduce rounding at segment boundaries.
        if (abs(got - expected) > max(.8, len(paths)*.12)
                or not any(v.get("codec_type") == "audio" for v in streams)):
            raise RuntimeError(f"Concatenação inconsistente: {got:.2f}s em vez de {expected:.2f}s")
        os.replace(tmp, output)
        stamp_cache(output, recipe)
    finally:
        if tmp.exists():
            tmp.unlink()

def add_music(video, song, output):
    length, _ = probe(video)
    if length <= 0:
        raise ValueError("Vídeo sem duração antes da mixagem")
    recipe = fingerprint(PIPELINE_VERSION, "music", source_stamp(video),
                         source_stamp(song), .30)
    if cache_ready(output, recipe, length):
        print("  REUTILIZAR mixagem musical", flush=True)
        return True
    tmp = output.with_name(output.stem + "_PARCIAL.mp4")
    fade_out_at = max(0, length - 1.5)
    # The scene's dialogue, if any, stays at its original level. No invented voices.
    filt = (f"[0:a]volume=1.0[a];"
            f"[1:a]volume=0.30,afade=t=in:st=0:d=0.6,"
            f"afade=t=out:st={fade_out_at:.3f}:d=1.5[m];"
            f"[a][m]amix=inputs=2:duration=first:normalize=0:"
            f"dropout_transition=0[ou]")
    try:
        cmd(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y",
             "-i", video, "-stream_loop", "-1", "-i", song,
             "-filter_complex", filt, "-map", "0:v:0", "-map", "[ou]",
             "-t", f"{length:.4f}", "-c:v", "copy", "-c:a", "aac",
             "-b:a", "160k", "-ar", "48000", "-ac", "2",
             "-movflags", "+faststart", tmp], f"Mixagem musical: {song.name}")
        got, streams = probe(tmp)
        if abs(got - length) > .7 or not any(s.get("codec_type") == "audio" for s in streams):
            raise RuntimeError("Mixagem inválida")
        os.replace(tmp, output)
        stamp_cache(output, recipe)
        return True
    finally:
        if tmp.exists():
            tmp.unlink()

def make_credits(cache):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as e:
        raise RuntimeError("Pillow ausente: py -3 -m pip install -r requirements.txt") from e
    cache.mkdir(exist_ok=True, parents=True)
    out = cache / "creditos.png"
    black = cache / "preto.png"
    if not out.exists():
        im = Image.new("RGB", (1920, 1080), (7, 8, 11))
        d = ImageDraw.Draw(im)
        font_name = "C:/Windows/Fonts/georgia.ttf"
        font = ImageFont.truetype(font_name, 88) if Path(font_name).exists() else ImageFont.load_default()
        font2_name = "C:/Windows/Fonts/arial.ttf"
        font2 = ImageFont.truetype(font2_name, 35) if Path(font2_name).exists() else ImageFont.load_default()
        d.text((960, 400), "ENTRE AMIGOS", font=font, anchor="mm", fill=(238, 236, 229))
        d.text((960, 520), "TURMA DE 2024", font=font2, anchor="mm", fill=(190, 185, 173))
        d.text((960, 750), "Uma história registrada por quem viveu", font=font2,
               anchor="mm", fill=(188, 181, 173))
        im.save(out)
    if not black.exists():
        Image.new("RGB", (1920, 1080), "black").save(black)
    return [(out, 7), (black, 2)]

def scenes_with_extras(scenes, idx, allow_large):
    # Acrescenta tomadas de acervo REAL ainda não usadas. A seleção por data é
    # PROVISÓRIA e pode conter bastidores. Áudio dessas extras fica em silêncio.
    assigned = {canon(clip["arquivo"]) for scene in scenes for clip in scene.get("clipes", [])}
    buckets = {2:["C08"],3:["C10"],4:["C13","C14"],5:["C13","C14"],
               6:["C16","C17","C18"],7:["C18","C19"],
               8:["C20","C21","C22","C23"],9:["C24","C25"],
               10:["C24","C25"],11:["C25","C28"],12:["C30","C31"]}
    by_id = {sc["id"]:sc for sc in scenes}
    candidates = {}
    for key, p in idx.items():
        if key in assigned or p.suffix.lower() not in VIDEO_EXT or not re.match(r"^2024(0[2-9]|1[0-2])\d{2}_", key):
            continue
        if not allow_large and p.stat().st_size > 268435456:
            continue
        if "abertura coletiva" in canon(str(p)) or "a classificar" in canon(str(p)):
            continue
        month = int(key[4:6])
        candidates.setdefault(month, []).append(p)
    added = set()
    for month, ids in buckets.items():
        for p in sorted(candidates.get(month, []), key=lambda f:f.name):
            available = [(by_id[s], s) for s in ids if s in by_id]
            available.sort(key=lambda x: sum(float(c.get("limite", 12)) for c in x[0]["clipes"])
                                      / max(1, x[0].get("alvo_segundos", 1)))
            for scene, _ in available:
                used = sum(float(c.get("limite", 12)) for c in scene["clipes"])
                if used >= float(scene.get("alvo_segundos") or 0):
                    continue
                if p.name in added:
                    continue
                scene["clipes"].append({"arquivo":p.name,"entrada":1.5,"saida":None,
                    "limite":11.5,"audio":"mute",
                    "status":"extra_por_data_provisoria_revisar"})
                added.add(p.name)
                break
    return len(added)

def render_credit_scene(cache, chunks, images):
    output = []
    for i,(photo,sec) in enumerate(make_credits(images)):
        part = chunks / f"C33_{i:02d}.mp4"
        render_clip(photo, {"entrada":0,"saida":None,"limite":sec,"audio":"mute"},
                    part, images)
        output.append(part)
    return output

def main():
    parser = argparse.ArgumentParser(description="ENTRE AMIGOS, montagem V1 em 33 cenas")
    parser.add_argument("--midias", required=True, help="Pasta local espelhada do Google Drive")
    parser.add_argument("--blocos", default=str(BASE / "blocos"),
                        help="Pasta com BLOCO_01.mp4 e BLOCO_02.mp4 exportados do Descript")
    parser.add_argument("--saida", default=str(BASE / "saida"))
    parser.add_argument("--verificar", action="store_true", help="Somente conferir arquivos")
    parser.add_argument("--extras", action="store_true",
                        help="Usar imagens extras não repetidas, por data e sem áudio; revisar")
    parser.add_argument("--incluir-grandes", action="store_true",
                        help="Permitir arquivos acima de 256 MiB nas extras")
    args = parser.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ERRO: FFmpeg e FFprobe precisam estar no PATH do Windows.")
        return 2
    project = json.loads((BASE / "projeto_v1.json").read_text(encoding="utf-8"))
    scenes = project["cenas"]
    if len(scenes) != 33:
        print("ERRO: manifesto sem as 33 cenas")
        return 2
    blocks = Path(args.blocos)
    idx = index_files(args.midias, blocks)
    mandatory = [asset(idx, x) for x in project["arquivos_obrigatorios"]]
    if not all(mandatory):
        print("FALTAM blocos obrigatórios do Descript:")
        for name, p in zip(project["arquivos_obrigatorios"],mandatory):
            print("  ", name, "OK" if p else "AUSENTE")
        print("Baixe os dois MP4 publicados no Descript e salve na pasta 'blocos'.")
        return 2
    if args.extras:
        count = scenes_with_extras(scenes, idx, args.incluir_grandes)
        print(f"Tomadas extras reais e únicas por data: {count} (provisórias)")
    missing = []
    sources = 0
    for s in scenes:
        if s["modo"] != "montar":
            continue
        for cut in s["clipes"]:
            if asset(idx, cut["arquivo"]):
                sources += 1
            else:
                missing.append((s["id"], cut["arquivo"]))
    print(f"Cenas do manifesto: {len(scenes)}; fontes de cenas restantes presentes: {sources}; ausentes: {len(missing)}")
    for sid, name in missing:
        print("  AUSENTE", sid, name)
    if args.verificar:
        print("CONFERÊNCIA FINALIZADA. Nenhum vídeo renderizado.")
        return 0
    output_root = Path(args.saida).resolve()
    chunk_dir = output_root / "segmentos"
    scenes_dir = output_root / "cenas"
    image_dir = output_root / "imagens_convertidas"
    for d in (chunk_dir,scenes_dir,image_dir):
        d.mkdir(exist_ok=True,parents=True)
    completed = []
    journal = output_root / "PROGRESSO.json"
    errors = []
    # A abertura aprovada já está incluída no BLOCO_01. Não duplicar.
    rendered = set()
    for scene in scenes:
        sid = scene["id"]
        mode = scene["modo"]
        if mode == "dentro_bloco01" or mode == "dentro_bloco02":
            continue
        scene_file = scenes_dir / (sid + ".mp4")
        if scene_file.is_file() and scene_file.stat().st_size > 16000:
            print("REUTILIZAR cena renderizada", sid)
            rendered.add(sid)
            completed.append(scene_file)
            continue
        try:
            if mode in ("bloco01","bloco02"):
                src = mandatory[0 if mode == "bloco01" else 1]
                parts = [chunk_dir / f"{sid}_bloco.mp4"]
                clip = {"entrada":0,"saida":None,"limite":probe(src)[0],"audio":"original"}
                render_clip(src,clip,parts[0],image_dir)
            elif mode == "creditos":
                parts = render_credit_scene(image_dir,chunk_dir,image_dir)
            else:
                parts = []
                for j,cut in enumerate(scene["clipes"]):
                    src = asset(idx, cut["arquivo"])
                    if src is None:
                        continue
                    part = chunk_dir / f"{sid}_{j:03d}.mp4"
                    if render_clip(src,cut,part,image_dir) > 0:
                        parts.append(part)
            if not parts:
                errors.append(f"{sid}: sem material acessível")
                continue
            neutral = scene_file if not scene.get("musica") or mode in ("bloco01","bloco02") else scene_file.with_name(sid+"_sem_trilha.mp4")
            concat_copy(parts,neutral)
            song = music_asset(idx, project["musicas_encontrar_por_nome"].get(scene.get("musica"),[]))
            if song and neutral != scene_file:
                add_music(neutral,song,scene_file)
            elif neutral != scene_file:
                shutil.move(neutral,scene_file)
                errors.append(f"{sid}: música '{scene.get('musica')}' ausente, cena sem trilha")
            seconds, _ = probe(scene_file)
            if seconds > 0:
                completed.append(scene_file)
                rendered.add(sid)
                print(f"  CONCLUÍDO {sid} ({seconds:.1f}s)",flush=True)
            else:
                errors.append(f"{sid}: arquivo exportado sem duração")
        except Exception as e:
            errors.append(f"{sid}: {type(e).__name__}: {e}")
            print("  FALHA",errors[-1],flush=True)
        finally:
            journal.write_text(json.dumps({"progresso":[x.stem for x in completed],
                "pendencias":errors,"fontes_faltando":missing},ensure_ascii=False,indent=2),encoding="utf-8")
    if not completed:
        print("Nenhuma cena finalizada, verifique PROGRESSO.json.")
        return 3
    final_file = output_root / "ENTRE_AMIGOS_V1_REVISAO.mp4"
    print("JUNTANDO",len(completed),"segmentos de cenas; sem repetir planos")
    concat_copy(completed, final_file)
    duration,streams = probe(final_file)
    vid = next((s for s in streams if s.get("codec_type") == "video"),{})
    print("Arquivo criado:",final_file)
    print("Duração real:",round(duration,2),"segundos, ou",round(duration/60,2),"minutos")
    print("Formato:",vid.get("width"),"x",vid.get("height"),"FR",vid.get("r_frame_rate"))
    print("Pendências:",len(errors),"; fontes ausentes:",len(missing))
    result = {"arquivo":str(final_file),"duracao_segundos":duration,
              "cenas_com_midia":sorted(rendered),"pendencias":errors,"fontes_ausentes":missing}
    (output_root/"RESULTADO.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    if duration < 1 or vid.get("width") != 1920 or vid.get("height") != 1080:
        print("ATENÇÃO: saída não passou pela conferência de resolução e duração")
        return 4
    print("OK: MP4 H264/AAC estruturado. Revisão editorial e escuta ainda necessárias.")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("ERRO DE EXECUÇÃO:",repr(exc))
        sys.exit(1)
