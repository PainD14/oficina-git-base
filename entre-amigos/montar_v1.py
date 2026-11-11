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
PIPELINE_VERSION = "2026-11-11-v3-complementos"

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

    # Complementos editoriais são exibidos APÓS os blocos fechados do Descript.
    # Não adicionam C34, nem repetem C01-C08/C09-C12 que já estão dentro dos MP4.
    extras = project.get("complementos_de_bloco", [])
    if not isinstance(extras, list):
        raise ValueError("complementos_de_bloco deve ser uma lista")
    seen_ids = set(ids)
    seen_cuts = {}
    for item in [*scenes, *extras]:
        for clip in item.get("clipes", []):
            name = canon(clip["arquivo"])
            start = float(clip.get("entrada") or 0)
            stop = clip.get("saida")
            if stop is not None:
                stop = float(stop)
                for old_start, old_stop, old_id in seen_cuts.get(name, []):
                    if old_stop is not None and start < old_stop and old_start < stop:
                        raise ValueError(f"Tomadas sobrepostas do mesmo arquivo: {name} ({item['id']} e {old_id})")
            seen_cuts.setdefault(name, []).append((start, stop, item["id"]))
    for item in extras:
        cid = item.get("id")
        if not cid or cid in seen_ids:
            raise ValueError(f"ID duplicado ou inválido em complemento: {cid}")
        seen_ids.add(cid)
        if item.get("modo") != "montar" or item.get("apos") not in {"C01", "C09"}:
            raise ValueError(f"Complemento {cid} deve ser montado após Bloco 01 ou Bloco 02")
        if item.get("cena_de_destino") not in ids:
            raise ValueError(f"Complemento {cid}: cena_de_destino inválida")
        for c in item.get("clipes", []):
            if c.get("saida") is None:
                raise ValueError(f"Complemento {cid} exige IN/OUT definidos")
            if not c.get("audio_original_presente", False):
                raise ValueError(f"Complemento {cid} ainda não tem áudio confirmado")
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
    signature = hashlib.sha1(json.dumps(source_stamp(source)).encode()).hexdigest()[:14]
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
    return start, max(0, min(available, length - start))

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
        if clip.get("audio") == "original" and not has_audio:
            raise RuntimeError(f"Áudio original exigido, mas ausente: {src.name}")
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
    """Only explicit, content-reviewed extras. Never auto-select by date alone."""
    file = BASE / "selecoes_adicionais_aprovadas.json"
    if not file.is_file():
        raise FileNotFoundError(
            "Para --extras, crie selecoes_adicionais_aprovadas.json com cortes "
            "revisados de ouvido e visualmente. Extras por data foram desativadas.")
    data = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("cenas"), dict):
        raise ValueError("Seleções adicionais: esperado {'cenas': {'C22': [...]}}")
    by_id = {s["id"]: s for s in scenes}
    selected = []
    used = {(canon(c["arquivo"]), c.get("entrada"), c.get("saida"))
            for s in scenes for c in s.get("clipes", [])}
    for sid, clips in data["cenas"].items():
        if sid not in by_id or by_id[sid]["modo"] != "montar":
            raise ValueError(f"Cena inválida para extras: {sid}")
        for cut in clips:
            if cut.get("revisado") is not True or cut.get("status") != "conteudo_conferido":
                raise ValueError(f"Extra de {sid} precisa da confirmação de conteúdo")
            if cut.get("saida") is None or float(cut["saida"]) <= float(cut.get("entrada") or 0):
                raise ValueError(f"Extra de {sid} precisa de IN e OUT revisados")
            path = asset(idx, cut["arquivo"])
            if not path:
                raise FileNotFoundError(f"Extra ausente: {cut['arquivo']}")
            if not allow_large and path.stat().st_size > 268435456:
                raise ValueError(f"Extra grande requer --incluir-grandes: {path.name}")
            key = (canon(cut["arquivo"]), cut["entrada"], cut["saida"])
            if key in used:
                raise ValueError(f"Corte duplicado em extra: {sid} {cut['arquivo']}")
            used.add(key)
            by_id[sid]["clipes"].append({k: v for k, v in cut.items() if k != "revisado"})
            selected.append(key)
    return len(selected)


def render_credit_scene(cache, chunks, images):
    output = []
    for i,(photo,sec) in enumerate(make_credits(images)):
        part = chunks / f"C33_{i:02d}.mp4"
        render_clip(photo, {"entrada":0,"saida":None,"limite":sec,"audio":"mute"},
                    part, images)
        output.append(part)
    return output

def save_json_atomic(dest, data):
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".tmp")
    partial.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(partial, dest)

def print_preflight(project, scenes, idx, blocks, estimated=True):
    missing, missing_music = [], []
    estimated_seconds = 9.0
    mandatory_names = project["arquivos_obrigatorios"]
    mandatory = [asset(idx, name) for name in mandatory_names]
    for name, file in zip(mandatory_names, mandatory):
        print(f"  BLOCO OBRIGATÓRIO {name}: {'OK' if file else 'AUSENTE'}")
        if file:
            dur, streams = probe(file)
            if not any(x.get("codec_type") == "video" for x in streams) or not any(x.get("codec_type") == "audio" for x in streams):
                missing.append(("blocos", f"{name}: arquivo sem áudio ou vídeo"))
            estimated_seconds += dur
        else:
            missing.append(("blocos", name))
    for scene in scenes:
        if scene["modo"] != "montar":
            continue
        for cut in scene["clipes"]:
            file = asset(idx, cut["arquivo"])
            if file is None:
                missing.append((scene["id"], cut["arquivo"]))
                continue
            if estimated:
                if file.suffix.lower() in IMAGE_EXT:
                    estimated_seconds += float(cut.get("limite") or 4.0)
                else:
                    start = float(cut.get("entrada") or 0)
                    nominal = float(cut["saida"])-start if cut.get("saida") is not None else float(cut.get("limite") or 12)
                    estimated_seconds += max(0, nominal)
        if scene.get("musica"):
            aliases = project["musicas_encontrar_por_nome"].get(scene["musica"], [])
            song = music_asset(idx, aliases)
            if not song and scene["id"] != "C26":
                missing_music.append((scene["id"], scene["musica"]))
            elif not song:
                print("  AVISO C26: trilha opcional O Caderno indisponível; cena sem música")
    print(f"\nESTIMATIVA SUPERIOR baseada em cortes programados: {estimated_seconds/60:.1f} minutos.")
    print("Não é a duração medida da saída: arquivos curtos e quadros finais podem reduzir a duração.")
    print(f"Fontes obrigatórias ausentes: {len(missing)}; músicas ausentes: {len(missing_music)}")
    for sid, name in missing:
        print("  FALTA", sid, name)
    for sid, song in missing_music:
        print("  FALTA MÚSICA", sid, song)
    return mandatory, missing, missing_music, estimated_seconds

def main():
    parser = argparse.ArgumentParser(description="ENTRE AMIGOS, montagem V1 das 33 cenas")
    parser.add_argument("--midias", required=True, help="Pasta local espelhada do Google Drive")
    parser.add_argument("--blocos", default=str(BASE / "blocos"),
                        help="Pasta com BLOCO_01.mp4 e BLOCO_02.mp4 exportados do Descript")
    parser.add_argument("--saida", default=str(BASE / "saida"))
    parser.add_argument("--verificar", action="store_true", help="Checar manifesto, caminhos e blocos sem renderizar")
    parser.add_argument("--extras", action="store_true",
                        help="Usar APENAS cortes confirmados em selecoes_adicionais_aprovadas.json")
    parser.add_argument("--incluir-grandes", action="store_true",
                        help="Permitir arquivos acima de 256 MiB nas extras revisadas")
    parser.add_argument("--permitir-incompleto", action="store_true",
                        help="Exportar _PARCIAL.mp4 mesmo faltando cenas ou músicas, nunca como V1 final")
    args = parser.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ERRO: FFmpeg e FFprobe não estão no PATH do Windows.")
        return 2
    project = json.loads((BASE / "projeto_v1.json").read_text(encoding="utf-8"))
    validate_manifest(project)
    scenes = project["cenas"]
    blocks = Path(args.blocos).resolve()
    idx = index_files(args.midias, blocks)
    if args.extras:
        count = scenes_with_extras(scenes, idx, args.incluir_grandes)
        print(f"Extras revisadas incluídas: {count}")
    complements = project.get("complementos_de_bloco", [])
    mandatory, missing, missing_music, estimate = print_preflight(
        project, scenes + complements, idx, blocks)
    if args.verificar:
        print("CONFERÊNCIA FINALIZADA. Nenhum vídeo foi renderizado.")
        return 2 if (missing or missing_music) else 0
    if missing or missing_music:
        if not args.permitir_incompleto or any(x[0] == "blocos" for x in missing):
            print("ERRO: arquivos obrigatórios indisponíveis. Nenhuma renderização iniciada.")
            return 2
        print("AVISO: saída PARCIAL explicitamente autorizada, há fontes ausentes.")
    output_root = Path(args.saida).resolve()
    chunk_dir, scenes_dir, image_dir = (output_root / "segmentos", output_root / "cenas",
                                         output_root / "imagens_convertidas")
    for d in (chunk_dir, scenes_dir, image_dir):
        d.mkdir(exist_ok=True, parents=True)
    errors, completed, rendered = [], [], set()
    journal = output_root / "PROGRESSO.json"
    # Cada bloco fechado entra uma vez; complementos de seus capítulos vêm depois
    # do bloco inteiro, em posição explícita, antes das próximas cenas.
    plan = []
    for scene in scenes:
        if scene["modo"] in ("dentro_bloco01", "dentro_bloco02"):
            continue
        plan.append(scene)
        plan.extend(comp for comp in complements if comp["apos"] == scene["id"])
    for sequence, scene in enumerate(plan, start=1):
        sid, mode = scene["id"], scene["modo"]
        scene_file = scenes_dir / f"{sid}.mp4"
        print(f"\n[{sequence}/{len(plan)}] {sid} - {scene['titulo']}", flush=True)
        try:
            if mode in ("bloco01", "bloco02"):
                original = mandatory[0 if mode == "bloco01" else 1]
                if original is None:
                    raise FileNotFoundError(f"Bloco {sid} ausente")
                parts = [chunk_dir / f"{sid}_bloco.mp4"]
                cut = {"entrada": 0, "saida": None, "limite": probe(original)[0], "audio": "original"}
                render_clip(original, cut, parts[0], image_dir)
            elif mode == "creditos":
                parts = render_credit_scene(image_dir, chunk_dir, image_dir)
            else:
                parts = []
                for j, cut in enumerate(scene["clipes"]):
                    source = asset(idx, cut["arquivo"])
                    if source is None:
                        errors.append(f"{sid}: arquivo ausente {cut['arquivo']}")
                        continue
                    target = chunk_dir / f"{sid}_{j:03d}.mp4"
                    render_clip(source, cut, target, image_dir)
                    parts.append(target)
            if not parts:
                raise RuntimeError("Nenhuma tomada válida disponível")
            song_name = scene.get("musica")
            neutral = scene_file if not song_name or mode in ("bloco01", "bloco02") \
                else scenes_dir / f"{sid}_sem_trilha.mp4"
            concat_copy(parts, neutral)
            if song_name and neutral != scene_file:
                song = music_asset(idx, project["musicas_encontrar_por_nome"].get(song_name, []))
                if song is None and sid == "C26":
                    print("  C26: O Caderno é opcional, mantendo vídeo com áudio neutro")
                    concat_copy([neutral], scene_file)
                elif song is None:
                    raise FileNotFoundError(f"Música ausente: {song_name}")
                else:
                    add_music(neutral, song, scene_file)
            dur, streams = probe(scene_file)
            if dur < .45 or not any(x.get("codec_type") == "audio" for x in streams):
                raise RuntimeError("Cena sem duração ou sem trilha de áudio")
            completed.append(scene_file)
            rendered.add(sid)
            print(f"  CENA CONCLUÍDA: {sid} ({dur:.2f}s)", flush=True)
        except Exception as e:
            errors.append(f"{sid}: {type(e).__name__}: {e}")
            print("  FALHA", errors[-1], flush=True)
        finally:
            save_json_atomic(journal, {
                "versao_motor": PIPELINE_VERSION,
                "cenas_concluidas": sorted(rendered),
                "cenas_previstas": len(plan),
                "pendencias": errors,
                "fontes_ausentes": missing,
                "musicas_ausentes": missing_music,
                "status": "em_progresso",
            })
    if errors or len(completed) != len(plan):
        print(f"\nMONTAGEM INCOMPLETA: {len(completed)}/{len(plan)} composições concluídas.")
        if not args.permitir_incompleto:
            save_json_atomic(journal, {"status": "incompleto", "cenas_concluidas": sorted(rendered),
                                       "pendencias": errors})
            print("O MP4 final NÃO será gerado. Corrija e execute o BAT novamente.")
            return 3
    if not completed:
        print("Nenhuma cena finalizada")
        return 3
    is_partial = bool(errors or missing or missing_music)
    name = "ENTRE_AMIGOS_V1_PARCIAL.mp4" if is_partial else "ENTRE_AMIGOS_V1_REVISAO.mp4"
    final_file = output_root / name
    print(f"\nJUNTAR {len(completed)} composições em {name}")
    concat_copy(completed, final_file)
    duration, streams = probe(final_file)
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    result = {"arquivo": str(final_file), "duracao_segundos": duration,
              "duracao_minutos": round(duration/60, 2),
              "cenas_com_midia": sorted(rendered), "pendencias": errors,
              "fontes_ausentes": missing, "musicas_ausentes": missing_music,
              "completo_tecnicamente": not is_partial}
    save_json_atomic(output_root / "RESULTADO.json", result)
    valid = (duration > 1 and video.get("width") == 1920
             and video.get("height") == 1080 and bool(audio))
    save_json_atomic(journal, {**result, "status": "renderizado" if valid and not is_partial else "parcial"})
    print(f"Arquivo: {final_file}\nDuração REAL: {duration/60:.2f} minutos")
    print(f"Resolução: {video.get('width')}x{video.get('height')}; áudio: {bool(audio)}")
    if not valid:
        print("ERRO: a exportação não passou na verificação básica de A/V")
        return 4
    print("MP4 técnico exportado. Revisão humana de diálogos, músicas e cortes ainda necessária.")
    return 0 if not is_partial else 5

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("ERRO DE EXECUÇÃO:", repr(exc))
        sys.exit(1)
