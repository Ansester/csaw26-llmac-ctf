#!/usr/bin/env python3
"""hemispheres solver. Usage: solve_hemispheres.py [png]   (needs Pillow)
PNG||ZIP polyglot; ZIP password hidden in blue-channel LSBs (16-bit BE length + bytes)."""
import os, sys, struct, zipfile
from PIL import Image

def b2b(bits):
    return bytes(int("".join(map(str, bits[i:i+8])), 2) for i in range(0, len(bits) // 8 * 8, 8))

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "hemispheres_the_signal.png")
data = open(path, "rb").read()
iend = data.rfind(b"IEND")
print("bytes after IEND chunk:", len(data) - (iend + 8), "| starts with", data[iend+8:iend+12])
img = Image.open(path).convert("RGB")
bits = [p & 1 for p in img.tobytes()[2::3]]
n = struct.unpack(">H", b2b(bits[:16]))[0]
pw = b2b(bits[16:16 + 8 * n])
print("LSB password:", pw)
with zipfile.ZipFile(path) as z:   # zipfile locates EOCD from end of file
    print("entries:", z.namelist())
    print("FLAG:", z.read("flag.txt", pwd=pw).decode().strip())
