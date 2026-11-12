#!/usr/bin/env python3
"""Autobahn solver: statically reproduce nitro's self-decryption (no execution).
Usage: python3 solve_autobahn.py [path/to/nitro]   (default: ./autobahn/nitro next to this script)"""
import os, struct, sys

SMC_KEY = bytes([0x13, 0x37, 0xC0, 0xDE, 0xBA, 0xAD, 0xF0, 0x0D])

def sections(d):
    shoff, = struct.unpack_from("<Q", d, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", d, 0x3A)
    hdrs = [struct.unpack_from("<IIQQQQIIQQ", d, shoff + i * shentsize) for i in range(shnum)]
    stro = hdrs[shstrndx][4]
    out = {}
    for h in hdrs:
        n = d[stro + h[0]:d.index(b"\0", stro + h[0])].decode()
        out[n] = (h[4], h[5])  # file offset, size
    return out

def main():
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "autobahn", "nitro")
    d = open(p, "rb").read()
    s = sections(d)
    o, n = s["enccode"]
    code = bytes(b ^ SMC_KEY[i % 8] for i, b in enumerate(d[o:o + n]))   # the self-rewrite
    # password: movb $imm, disp(%rbp)  (C6 45 disp imm)
    pw, i = bytearray(), 0
    while i < len(code) - 3:
        if code[i] == 0xC6 and code[i + 1] == 0x45:
            if code[i + 3] == 0: break
            pw.append(code[i + 3]); i += 4
        else:
            i += 1
    print("password:", pw.decode())
    # keystream derived from the DECRYPTED code: k[i] = code[(7i+3)%L] + 5i + 0x6b
    ks = bytes((code[(i * 7 + 3) % n] + i * 5 + 0x6B) & 0xFF for i in range(128))
    o, n2 = s[".rodata"]
    ro = d[o:o + n2]
    for st in range(len(ro) - 5):
        if bytes(ro[st + j] ^ ks[j] for j in range(5)) == b"csaw{":
            f = bytearray()
            for j in range(len(ks)):
                c = ro[st + j] ^ ks[j]; f.append(c)
                if c == ord("}"): break
            print("flag:", f.decode()); return
    sys.exit("flag not found")

main()
