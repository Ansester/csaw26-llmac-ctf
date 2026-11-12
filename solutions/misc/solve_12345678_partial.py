#!/usr/bin/env python3
"""12345678 -- PARTIAL. Reproduces the two flag fragments that were recovered; see BLOCKER_12345678.md.
Usage: python3 solve_12345678_partial.py "12345678 (1).wav"      (needs numpy)
"""
import sys, struct, base64
import numpy as np
raw = open(sys.argv[1], 'rb').read()

# fragment A: RIFF LIST/INFO ICRD (and identical ID3 TDRC) holds base64
p = 12; ch = {}
while p < len(raw):
    cid, sz = raw[p:p+4], struct.unpack('<I', raw[p+4:p+8])[0]; ch[cid] = (p + 8, sz); p += 8 + sz + (sz & 1)
lo, ls = ch[b'LIST']; blob = raw[lo:lo+ls]; i = blob.find(b'ICRD'); n = struct.unpack('<I', blob[i+4:i+8])[0]
b64 = blob[i+8:i+8+n].rstrip(b'\0'); print('ICRD base64:', b64.decode(), '->', base64.b64decode(b64).decode())

# fragment B: a 7-row bitmap font drawn with tones at 880..3520 Hz (multiples of 440) in the right channel, ~22.7-24.1 s
do, ds = ch[b'data']; pcm = np.frombuffer(raw[do:do+ds], '<i2').reshape(-1, 2); sr = 44100
x = pcm[:, 1].astype(float); freqs = [440 * k for k in range(2, 9)]; W = 441; tt = np.arange(W) / sr
cols = []
for k in range(0, 76):                                   # 20 ms per pixel column
    s = int((22.70 + 0.02 * k) * sr) - W // 2; seg = x[s:s+W] * np.hanning(W)
    cols.append([abs(np.sum(seg * np.exp(-2j * np.pi * f * tt))) for f in freqs])
C = np.array(cols) > np.array(cols).max() * 0.25
print('tone bitmap (rows 3520..880 Hz, 20 ms/column); read left to right it spells a base64 string:')
for r in range(6, -1, -1): print(''.join('#' if C[c][r] else ' ' for c in range(len(C))))
print('read from the high-resolution rendering: dV9uMzNkXw== ->', base64.b64decode('dV9uMzNkXw==').decode())
print('fragments so far: ..., %s, %s, ...' % (base64.b64decode(b64).decode(), base64.b64decode('dV9uMzNkXw==').decode()))
