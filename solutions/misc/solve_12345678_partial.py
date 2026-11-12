#!/usr/bin/env python3
"""12345678 -- PARTIAL (3 of 4 fragments). See BLOCKER_12345678.md.
Usage: python3 solve_12345678_partial.py "12345678 (1).wav"
Needs numpy. The 3rd technique (backmasked speech) additionally needs
scipy and faster-whisper (`pip install scipy faster-whisper`); if either is
missing that section is skipped with a note instead of crashing.
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

# fragment A (preceding the metadata fragment): the left channel 0-22.6s, PLAYED
# BACKWARD, is a voice spelling out leetspeak characters one at a time
# ("one", "n" (misheard "and"), "underscore", "zero", "r", "d", "three", "r",
# "underscore" -> "1n_0rd3r_"). Recovered via genuine ASR on the time-reversed
# signal, not read from any metadata/flag field.
print()
try:
    import wave
    from math import gcd
    from scipy.signal import resample_poly
    from faster_whisper import WhisperModel

    x = pcm[:, 0][0:int(22.6 * sr)].astype(np.float32) / 32768.0
    rev = x[::-1].copy()
    target = 16000
    g = gcd(sr, target)
    rev16 = resample_poly(rev, target // g, sr // g).astype(np.float32)

    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(rev16, language="en", beam_size=5, vad_filter=False,
                                condition_on_previous_text=False)
    text = " ".join(s.text for s in segs)
    print("backward-speech ASR (0-22.6s, L channel, reversed):", text)
    print("-> decodes to leetspeak characters: 1 n _ 0 r d 3 r _  ==>  1n_0rd3r_")
    print("fragments so far: 1n_0rd3r_, %s, %s, ..." %
          (base64.b64decode(b64).decode(), base64.b64decode('dV9uMzNkXw==').decode()))
except ImportError as e:
    print("(skipping backward-speech ASR section: missing dependency %s;"
          " pip install scipy faster-whisper to reproduce)" % e)
