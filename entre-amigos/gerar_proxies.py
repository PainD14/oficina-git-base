#!/usr/bin/env python3
# Gera cópias LEVES para análise dos 20 originais >256 MiB. Nunca muda os originais.
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ALVOS = (
    "20241025_104359.mp4", "20240930_102000.mp4", "20240925_083607.mp4",
    "20240702_112028.mp4", "20240702_083556.mp4", "20240628_083553.mp4",
    "20240619_092726.mp4", "20240618_104253.mp4", "20240618_103950.mp4",
    "20240618_085447.mp4", "20240614_100338.mp4", "20240607_105635.mp4",
    "20240607_105455.mp4", "20240510_090507.mp4", "20240321_114137.mp4",
    "20240321_105845.mp4", "20240321_105545.mp4", "20240321_101623.mp4",
    "20241206_092404.mp4", "20241206_092640.mp4",
)

def call(args):
    r = subprocess.run([str(x) for x in args], capture_output=True, text=True, errors="replace")
    if r.returncode:
        raise RuntimeError(r.stderr[-1700:] or f"Comando terminou com {r.returncode}")
    return r.stdout

def probe(path):
    obj = json.loads(call(["ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height", "-of", "json", path]))
    streams = obj.get("streams", [])
    return float(obj.get("format", {}).get("duration") or 0), streams

def convert(source, dest, force=False):
    meta = dest.with_suffix(".origem.json")
    stat = source.stat()
    recipe = {"original": str(source.resolve()), "bytes": stat.st_size,
              "mtime_ns": stat.st_mtime_ns, "metodo": "720p-h264-aac-crf30"}
    original_dur, streams = probe(source)
    if original_dur <= 0 or not any(x.get("codec_type") == "video" for x in streams):
        raise RuntimeError("Original sem vídeo decodificável")
    if dest.exists() and meta.exists() and not force:
        try:
            saved = json.loads(meta.read_text(encoding="utf-8"))
            proxy_dur, proxy_streams = probe(dest)
            if (all(saved.get(x) == v for x, v in recipe.items())
                and abs(proxy_dur-original_dur) < .5
                and any(x.get("codec_type") == "video" for x in proxy_streams)):
                print("  REUTILIZAR proxy já conferido", flush=True)
                return saved
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
            pass
    temp = dest.with_name(dest.stem + "_PARCIAL.mp4")
    temp.parent.mkdir(parents=True, exist_ok=True)
    try:
        call(["ffmpeg","-hide_banner","-nostdin","-v","error","-y",
            "-i",source,"-map","0:v:0","-map","0:a:0?",
            "-vf","scale=1280:720:force_original_aspect_ratio=decrease,"
                  "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1",
            "-c:v","libx264","-preset","veryfast","-crf","30",
            "-pix_fmt","yuv420p","-c:a","aac","-b:a","96k",
            "-ar","48000","-ac","2","-movflags","+faststart",temp])
        proxy_dur, proxy_streams = probe(temp)
        if abs(proxy_dur-original_dur) >= .5 or not any(s.get("codec_type") == "video" for s in proxy_streams):
            raise RuntimeError("Duração/stream do proxy divergente da origem")
        if any(x.get("codec_type") == "audio" for x in streams) and not any(x.get("codec_type") == "audio" for x in proxy_streams):
            raise RuntimeError("Áudio original sumiu no proxy")
        os.replace(temp,dest)
        recipe.update({"duracao_original":original_dur,"duracao_proxy":proxy_dur,
                       "audio_presente":any(s.get("codec_type") == "audio" for s in proxy_streams),
                       "proxy":str(dest.resolve())})
        meta.write_text(json.dumps(recipe,ensure_ascii=False,indent=2),encoding="utf-8")
        return recipe
    finally:
        if temp.exists():
            temp.unlink()

def main():
    ap=argparse.ArgumentParser(description="ENTRE AMIGOS: gerar proxies 720p sem mexer nos originais")
    ap.add_argument("--midias",required=True,help="Pasta ORIGINAL espelhada do Google Drive")
    ap.add_argument("--dest",default=str(Path(__file__).resolve().parent/"proxies_para_decupagem"))
    ap.add_argument("--arquivos",nargs="*",help="Para teste: substituir a lista de 20 arquivos grandes")
    ap.add_argument("--refazer",action="store_true",help="Forçar novo proxy do mesmo original")
    args=ap.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("FALTA ffmpeg/ffprobe no PATH");return 2
    root=Path(args.midias).resolve()
    if not root.is_dir():
        print("PASTA não encontrada:",root);return 2
    dest=Path(args.dest).resolve();dest.mkdir(parents=True,exist_ok=True)
    targets=args.arquivos if args.arquivos else list(ALVOS)
    found={}
    for path in root.rglob("*"):
        if path.is_file() and path.name in targets:
            found.setdefault(path.name,[]).append(path)
    success=[]; errors=[]
    for i,name in enumerate(targets,1):
        print(f"\n[{i}/{len(targets)}] {name}",flush=True)
        paths=found.get(name,[])
        if len(paths)!=1:
            error="não localizado" if not paths else "duplicado em várias pastas; selecione uma origem"
            errors.append([name,error])
            print("  PENDENTE:",error,flush=True)
            continue
        try:
            meta=convert(paths[0],dest/(Path(name).stem+"_PROXY.mp4"),args.refazer)
            success.append(meta)
            print(f"  OK {meta.get('duracao_proxy',0):.2f}s",flush=True)
        except Exception as e:
            errors.append([name,str(e)])
            print("  ERRO:",str(e),flush=True)
        (dest/"INDICE_PROXIES.json").write_text(
            json.dumps({"concluidos":success,"pendencias":errors},ensure_ascii=False,indent=2),
            encoding="utf-8")
    print(f"\nProxies prontos: {len(success)}/{len(targets)}. Pasta: {dest}")
    print("Use os PROXIES apenas para analisar. O MP4 final deve usar os originais.")
    return 0 if not errors else 3

if __name__=="__main__":
    sys.exit(main())
