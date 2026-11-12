#!/usr/bin/env python3
"""finders_keepers solver.
Phase 1:  python solve_finders_keepers.py            -> extracts XMP dc:subject blob (base64 ciphertext) and dumps
          contrast crops of the video frames where a faint, rotated, drifting base64 string appears
          (finders_keepers_out/strip.png).  Read the string off the image (OCR of this drifting text is unreliable).
Phase 2:  python solve_finders_keepers.py <base64 read from frames>
          -> decodes it (the plaintext answer) and uses it as a Vigenere key (letters only) on the XMP blob.
Needs: pip install imageio-ffmpeg pillow   (bundled ffmpeg is used for frame extraction)
"""
import sys, os, re, base64, subprocess, glob
HERE = os.path.dirname(os.path.abspath(__file__))
MP4 = os.path.join(HERE, "finders_keepers_data", "finderskeepers.mp4")
OUT = os.path.join(HERE, "finders_keepers_out")

raw = open(MP4, "rb").read()
m = re.search(rb"<dc:subject>.*?<rdf:li>([A-Za-z0-9+/=]+)</rdf:li>", raw, re.S)
blob = base64.b64decode(m.group(1)).decode()
print("[xmp] dc:subject ->", m.group(1).decode(), "->", blob)


def vig_dec(ct, key):
    out, k = [], 0
    for ch in ct:
        if ch.isalpha():
            b = 97 if ch.islower() else 65
            out.append(chr((ord(ch) - b - (ord(key[k % len(key)].lower()) - 97)) % 26 + b)); k += 1
        else:
            out.append(ch)
    return "".join(out)


if len(sys.argv) < 2:
    import imageio_ffmpeg
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-i", MP4,
                    "-fps_mode", "passthrough", os.path.join(OUT, "f%03d.png")], check=True)
    picks = [211, 241, 271, 300]
    strip = Image.new("RGB", (800, 200 * len(picks)))
    for i, n in enumerate(picks):
        strip.paste(Image.open(os.path.join(OUT, f"f{n:03d}.png")).convert("RGB").crop((700, 60, 1500, 260)), (0, 200 * i))
    strip.save(os.path.join(OUT, "strip.png"))
    for f in glob.glob(os.path.join(OUT, "f*.png")): os.remove(f)
    print("[frames] wrote", os.path.join(OUT, "strip.png"), "- read the base64 text, rerun with it as argument")
else:
    msg = base64.b64decode(sys.argv[1]).decode()
    print("[video text] decoded plaintext (the answer to submit):", msg)
    print("[bonus] Vigenere(XMP blob, key=plaintext):", vig_dec(blob, msg))
