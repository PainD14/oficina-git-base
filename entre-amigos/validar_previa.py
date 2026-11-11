#!/usr/bin/env python3
"""Valida o MP4 real da montagem V1, decodifica A/V e publica a cópia de revisão.

Nunca gera o filme, duplica cenas ou modifica os dois blocos. Só copia o MP4
efetivamente exportado por montar_v1.py depois de validação.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent

def run(command):
    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, errors="replace", check=True)

def validate(src, dst, decode=True):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg/FFprobe não estão instalados ou não estão no PATH")
    if not src.is_file() or src.stat().st_size < 100000:
        raise RuntimeError(f"MP4 de origem ausente ou vazio: {src}")
    output = run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                  "-of", "json", str(src)])
    meta = json.loads(output.stdout)
    streams = meta.get("streams", [])
    vid = next((x for x in streams if x.get("codec_type") == "video"), None)
    aud = next((x for x in streams if x.get("codec_type") == "audio"), None)
    duration = float(meta.get("format", {}).get("duration") or 0)
    if not vid or not aud or duration <= 0:
        raise RuntimeError("O arquivo não tem vídeo, áudio ou duração válida")
    if (vid.get("width"), vid.get("height")) != (1920, 1080):
        raise RuntimeError("A imagem não está em Full HD 1920x1080")
    if vid.get("codec_name") != "h264" or aud.get("codec_name") != "aac":
        raise RuntimeError("Codecs diferentes de H.264/AAC, conferir a exportação")
    if decode:
        run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-xerror",
             "-i", str(src), "-map", "0:v:0", "-map", "0:a:0",
             "-f", "null", "-"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".parcial")
    try:
        shutil.copyfile(src, tmp)
        if tmp.stat().st_size != src.stat().st_size:
            raise RuntimeError("A cópia do MP4 foi interrompida")
        os.replace(tmp, dst)
    finally:
        if tmp.exists():
            tmp.unlink()
    print("MP4 CONFERIDO:", dst)
    print(f"DURAÇÃO REAL: {duration/60:.2f} minutos ({duration:.2f} segundos)")
    print("FORMATO: 1920x1080, vídeo H.264, áudio AAC")
    if not (18*60 <= duration <= 26*60):
        print("AVISO: duração fora da faixa aproximada de 22 minutos; não prolongar artificialmente.")
    print("A revisão das falas e dos cortes continua sendo necessária após assistir.")
    return duration

def main():
    p = argparse.ArgumentParser(description="Validação final da prévia ENTRE AMIGOS")
    p.add_argument("--origem", default=str(BASE / "saida" / "ENTRE_AMIGOS_V1_REVISAO.mp4"))
    p.add_argument("--destino", default=str(BASE / "saida" / "ENTRE_AMIGOS_V1_PREVIA_22MIN.mp4"))
    p.add_argument("--sem-decodificar", action="store_true", help="Somente testes sintéticos")
    args = p.parse_args()
    try:
        validate(Path(args.origem), Path(args.destino), not args.sem_decodificar)
        return 0
    except (RuntimeError, OSError, subprocess.CalledProcessError, ValueError) as error:
        print("FALHA NA VALIDAÇÃO DA PRÉVIA:", str(error))
        return 4

if __name__ == "__main__":
    sys.exit(main())
