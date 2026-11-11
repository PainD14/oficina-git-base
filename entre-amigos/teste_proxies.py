#!/usr/bin/env python3
# Smoke test de proxies: apenas material sintetico, nunca videos da turma.
from pathlib import Path
import subprocess
import tempfile
import gerar_proxies as p

def run(*args):
    subprocess.run([str(a) for a in args], check=True)

with tempfile.TemporaryDirectory(prefix="proxies-entre-amigos-") as temp:
    folder=Path(temp)
    src=folder/"teste.mp4"
    dst=folder/"proxies"/"teste_PROXY.mp4"
    run("ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","lavfi","-i","testsrc2=size=320x180:rate=24",
        "-f","lavfi","-i","sine=frequency=440:sample_rate=48000",
        "-t","1.6","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",src)
    orig_size=src.stat().st_size
    meta=p.convert(src,dst)
    assert dst.exists() and meta["audio_presente"]
    dur,streams=p.probe(dst)
    assert 1.3<dur<2
    vid=next(x for x in streams if x["codec_type"]=="video")
    assert vid["width"]==1280 and vid["height"]==720
    assert orig_size==src.stat().st_size,"Original foi alterado"
    marker=dst.stat().st_mtime_ns
    meta2=p.convert(src,dst)
    assert marker==dst.stat().st_mtime_ns,"Deveria reutilizar proxy valido"
    assert meta2["original"]==str(src.resolve())
    print("OK: proxy 720p H264/AAC, audio preservado, origem intacta e retomada")
