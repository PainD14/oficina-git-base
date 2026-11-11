#!/usr/bin/env python3
# Smoke test técnico com mídias SINTÉTICAS, sem vídeos do documentário.
from pathlib import Path
import subprocess
import tempfile
from PIL import Image
import montar_v1 as m

def run(*args):
    subprocess.run([str(x) for x in args], check=True)

with tempfile.TemporaryDirectory(prefix="entre-amigos-test-") as d:
    root=Path(d)
    source=root/"exemplo.mp4"
    tone=root/"musica_teste.wav"
    photo=root/"foto_exemplo.jpg"
    Image.new("RGB",(360,640),(52,70,92)).save(photo)
    run("ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","lavfi","-i","testsrc2=size=320x180:rate=24",
        "-f","lavfi","-i","sine=frequency=440:sample_rate=48000",
        "-t","2","-c:v","libx264","-pix_fmt","yuv420p",
        "-c:a","aac",source)
    run("ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","lavfi","-i","sine=frequency=220:sample_rate=48000",
        "-t","3",tone)
    take=root/"take.mp4"
    image=root/"imagem.mp4"
    m.render_clip(source,{"entrada":0.1,"saida":1.1,"audio":"original"},take,root/"imagens")
    m.render_clip(photo,{"limite":1.25,"audio":"mute"},image,root/"imagens")
    montage=root/"montagem.mp4"
    m.concat_copy([take,image],montage)
    mix=root/"montagem_com_trilha.mp4"
    assert m.add_music(montage,tone,mix)
    duration,streams=m.probe(mix)
    video=next(s for s in streams if s.get("codec_type")=="video")
    assert video["width"]==1920 and video["height"]==1080
    assert 2.0 < duration < 2.8, duration
    print("TESTE REAL COM FFmpeg OK, 1920x1080, duração",round(duration,3),"s")
