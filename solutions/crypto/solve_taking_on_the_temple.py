#!/usr/bin/env python3
"""Midnight Vault ("taking_on_the_temple") solver. Usage: python solve_taking_on_the_temple.py HOST PORT
Drives the live HTTP service: fetches each artifact only after the server unlocks it, decrypts it, and
lets the server's own accept/reject (and AES-GCM tag verification at the end) decide which marker is right.
No hardcoded markers/flag."""
import sys, re, json, base64, hashlib
import requests
from Crypto.Cipher import AES

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"
PORT = sys.argv[2] if len(sys.argv) > 2 else "5000"
BASE = f"http://{HOST}:{PORT}"
S = requests.Session()


def unlocked(path, answer):
    r = S.post(BASE + path, data={"answer": answer})
    return "RECOVERED" in r.text


def get(name):
    r = S.get(f"{BASE}/artifact/{name}")
    r.raise_for_status()
    return r.content


def autokey_decrypt(ct, primer):
    pt, key = [], "".join(c for c in primer.upper() if c.isalpha())
    for i, ch in enumerate(ct):
        shift = ord(key[i]) - 65 if i < len(key) else ord(pt[i - len(key)]) - 65
        pt.append(chr((ord(ch) - 65 - shift) % 26 + 65))
    return "".join(pt)


def unmirror(x, n):  # data was copied in reversed chunks of size n
    return x[:0].join(x[i:i + n][::-1] for i in range(0, len(x), n))


def xor_stream(data, material):
    out, ctr = bytearray(), 0
    while len(out) < len(data):
        blk = hashlib.sha256(material + ctr.to_bytes(8, "big")).digest()
        out += bytes(a ^ b for a, b in zip(data[len(out):len(out) + 32], blk))
        ctr += 1
    return bytes(out)


# ---- Stage 1: Granite (braille clue says STONE -> autokey primer; "mirrored trios" -> reverse each 3 chars)
page = S.get(BASE + "/stone").text
ct = re.search(r"Ciphertext:\s*([A-Z]+)", page).group(1)
pt1 = autokey_decrypt(unmirror(ct, 3), "STONE")
print("[1] plaintext:", pt1)
# Plaintext ends 'MARKER GRANITE'; numeric suffix is hinted only by the (decoy-laden) 'other markings'.
decoys = re.findall(r"^- (.+)$", page, re.M)
print("    other markings:", decoys)
nums = set(re.findall(r"\d+", " ".join(decoys)))
cands = ["GRANITE-" + n for n in sorted(nums)]
k1 = next((c for c in cands if unlocked("/stone", c)), None)
if k1 is None:
    sys.exit("stage 1 failed for candidates %s" % cands)
print("[1] server accepted:", k1)

# ---- Stage 2: Frost ("mirrored blocks" of 8 bytes, stream keyed by sha256(k1))
frost = unmirror(get("frost.bin"), 8)
pt2 = xor_stream(frost, hashlib.sha256(k1.encode()).digest()).decode()
print("[2] plaintext:\n" + pt2)
k2 = re.search(r"MARKER:\s*(\S+)", pt2).group(1)
assert unlocked("/frost", k2), "frost marker rejected"
print("[2] server accepted:", k2)

# ---- Stage 3: Iron (hash chain keys, base64 payload with mirrored quartets)
iron = json.loads(get("iron.json"))
h0 = hashlib.sha256(k2.encode()).digest()
h1 = hashlib.sha256(h0 + k1.encode()).digest()
h2 = hashlib.sha256(h1[::-1] + k2.encode()).digest()
pt3 = xor_stream(base64.b64decode(unmirror(iron["payload_b64"], 4)), h2).decode()
print("[3] plaintext:\n" + pt3)
k3 = re.search(r"MARKER:\s*(\S+)", pt3).group(1)
assert unlocked("/iron", k3), "iron marker rejected"
print("[3] server accepted:", k3)

# ---- Stage 4: Vault (AES-GCM; tag verification proves the key is right)
v = json.loads(get("vault.json"))
key = hashlib.sha256(k1.encode() + b"|" + k2.encode() + b"|" + k3.encode()).digest()
nonce = base64.b64decode(unmirror(v["nonce_b64"], 4))
blob = base64.b64decode(unmirror(v["ciphertext_b64"], 4))
c = AES.new(key, AES.MODE_GCM, nonce=nonce)
c.update(v["aad"].encode())
flag = c.decrypt_and_verify(blob[:-16], blob[-16:]).decode()
r = S.post(BASE + "/vault", data={"flag": flag})
print("[4] vault:", "OPEN" if "VAULT IS OPEN" in r.text else "REJECTED")
print("FLAG:", flag)
