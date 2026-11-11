#!/usr/bin/env python3
"""Smoke test sintético de validação da prévia, sem mídia real."""
import subprocess
import tempfile
from pathlib import Path
from validar_previa import validate

def run(*args):
    subprocess.run(list(map(str,args)),check=True)

with tempfile.TemporaryDirectory(prefix="entre_amigos_preview_") as td:
    d=Path(td)
    src=d/"sintetico_1080.mp4"
    dst=d/"ENTRE_AMIGOS_V1_PREVIA_22MIN.mp4"
    run("ffmpeg","-v","error","-y","-f","lavfi","-i",
        "testsrc2=size=1920x1080:rate=24","-f","lavfi","-i",
        "sine=frequency=440:sample_rate=48000","-t","1.2","-c:v",
        "libx264","-preset","ultrafast","-pix_fmt","yuv420p",
        "-c:a","aac","-ac","2",src)
    length=validate(src,dst)
    assert dst.exists() and dst.stat().st_size==src.stat().st_size
    assert 1 < length < 1.5
    no_audio=d/"sem_audio.mp4"
    run("ffmpeg","-v","error","-y","-f","lavfi","-i",
        "testsrc2=size=128x72:rate=24","-t","1",
        "-c:v","libx264","-pix_fmt","yuv420p",no_audio)
    try:
        validate(no_audio,d/"nao_deve_gerar.mp4")
        raise AssertionError("Deveria rejeitar exportação inválida")
    except RuntimeError:
        pass
    assert not (d/"nao_deve_gerar.mp4").exists()
    print("OK: MP4 Full HD com áudio validado e rejeição de exportação incompleta")
