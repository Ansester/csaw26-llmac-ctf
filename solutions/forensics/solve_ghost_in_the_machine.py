#!/usr/bin/env python3
"""ghost_in_the_machine solver. Usage: solve_ghost_in_the_machine.py [capture.pcap]
Stdlib only. Timing covert channel: filter by TTL, gaps->bits, XOR with key from UDP src ports."""
import os, struct, sys
from collections import Counter

def read_pcap(path):
    d = open(path, "rb").read()
    m = struct.unpack("<I", d[:4])[0]
    e = "<" if m in (0xA1B2C3C4, 0xA1B23C4D) else ">"
    nano = m in (0xA1B23C4D, 0x4D3CB2A1)
    off, out = 24, []
    while off + 16 <= len(d):
        s, f, il, _ = struct.unpack(e + "IIII", d[off:off+16]); off += 16
        fr = d[off:off+il]; off += il
        out.append((s + f / (1e9 if nano else 1e6), fr[22], struct.unpack("!H", fr[34:36])[0]))
    return out

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "ghost_capture.pcap")
    pk = read_pcap(path)
    ttls = Counter(p[1] for p in pk)
    print("TTL histogram:", dict(ttls))
    real_ttl = ttls.most_common(1)[0][0]   # majority = real carrier, minority = decoys
    real = sorted((p for p in pk if p[1] == real_ttl), key=lambda p: p[0])
    t = [p[0] for p in real]; sp = [p[2] for p in real]
    gaps = [b - a for a, b in zip(t, t[1:])]
    th = (min(gaps) + max(gaps)) / 2
    bits = [int(g > th) for g in gaps]
    ct = bytes(int("".join(map(str, bits[i:i+8])), 2) for i in range(0, len(bits) // 8 * 8, 8))
    # key byte j = src_port - 40000 of a packet in group j (packets 8j..8j+7)
    keys = [(sp[8*j + 1] - 40000) & 0xFF for j in range(len(ct))]
    print("key stream:", bytes(keys))
    print("FLAG:", bytes(c ^ k for c, k in zip(ct, keys)).decode(errors="replace"))
main()
