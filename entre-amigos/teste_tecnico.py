#!/usr/bin/env python3
# Smoke tests: only synthetic video/audio/image sources, never real students' recordings.
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from PIL import Image
import montar_v1 as m

def run(*args):
    subprocess.run([str(x) for x in args], check=True)

with tempfile.TemporaryDirectory(prefix="entre-amigos-test-") as d:
    root = Path(d)
    src = root / "exemplo.mp4"
    silent = root / "sem_audio.mp4"
    music = root / "musica_teste.wav"
    photo = root / "foto_exemplo.jpg"
    Image.new("RGB", (360, 640), (52, 70, 92)).save(photo)
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
        "-t", "2.1", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", src)
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30",
        "-t", "1.2", "-c:v", "libx264", "-pix_fmt", "yuv420p", silent)
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "sine=frequency=220:sample_rate=48000",
        "-t", "3", music)

    take, still, noaudio = root / "take.mp4", root / "foto.mp4", root / "silencioso.mp4"
    m.render_clip(src, {"entrada": .1, "saida": 1.1, "audio": "original"}, take, root / "imagens")
    m.render_clip(photo, {"limite": 1.25, "audio": "mute"}, still, root / "imagens")
    m.render_clip(silent, {"entrada": 0, "saida": 1, "audio": "original"}, noaudio, root / "imagens")
    for item in (take, still, noaudio):
        dur, streams = m.probe(item)
        assert dur >= .9
        assert next(s for s in streams if s["codec_type"] == "video")["width"] == 1920
        assert any(s["codec_type"] == "audio" for s in streams), item

    joined = root / "montagem.mp4"
    m.concat_copy([take, still, noaudio], joined)
    mixed = root / "montagem_com_trilha.mp4"
    assert m.add_music(joined, music, mixed)
    duration, streams = m.probe(mixed)
    assert 2.9 < duration < 3.7, duration
    assert any(s["codec_type"] == "audio" for s in streams)
    # Decode at least the entire short clip to catch broken muxing, not just metadata.
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", mixed,
        "-f", "null", "-")

    before = m.cache_marker(take).read_text(encoding="utf-8")
    m.render_clip(src, {"entrada": .1, "saida": .66, "audio": "original"}, take, root / "imagens")
    after = m.cache_marker(take).read_text(encoding="utf-8")
    assert before != after, "Uma alteração de timecode deve invalidar o segmento"
    m.concat_copy([take, still, noaudio], joined)
    assert m.add_music(joined, music, mixed)
    newduration, _ = m.probe(mixed)
    assert newduration < duration - .2, "Mudança de corte deve invalidar junção e mixagem"
    print("OK: render 1080p, áudio, foto vertical, vídeo silencioso, concatenação e invalidação")

    # Check strict preflight and the 33-scene structure.
    doc = json.loads((Path(__file__).parent / "projeto_v1.json").read_text(encoding="utf-8"))
    assert m.validate_manifest(doc)
    assert len(doc["cenas"]) == 33
    assert doc["cenas"][0]["modo"] == "bloco01"
    assert doc["cenas"][8]["modo"] == "bloco02"
    assert sum(s["modo"] == "montar" for s in doc["cenas"]) >= 20
    print("OK: 33 cenas, dois blocos sem duplicação, fontes de música definidas")
