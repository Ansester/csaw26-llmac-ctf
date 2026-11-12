#!/usr/bin/env python3
"""Machine Head solver: carve VM bytecode from the binary, emulate it, recover flag left-to-right.
Usage: python3 solve_machine_head.py [path/to/masterkey]  (default: ./machine_head/masterkey)"""
import os, sys
# opcode table recovered from the interpreter's switch
VLD, VXORI, VADDI, VMULI, VROL, VXORR, VADDR, VCMP, VHLT = 0x91, 0x7A, 0x24, 0x1D, 0xB2, 0x4E, 0x6D, 0xA7, 0xE0
VALID = {VLD, VXORI, VADDI, VMULI, VROL, VXORR, VADDR, VCMP, VHLT}
rol = lambda v, n: ((v << (n & 7)) | (v >> (8 - (n & 7)))) & 0xFF

def carve(b):
    best = b""
    for i in range(len(b) - 2):
        j = i
        while j + 2 < len(b) and b[j] in VALID and b[j] != VHLT: j += 3
        if j + 2 < len(b) and b[j] == VHLT and j + 3 - i > len(best): best = b[i:j + 3]
    return best

def run(code, inp):
    r = [0] * 8; res = []
    for pc in range(0, len(code), 3):
        op, a, b = code[pc:pc + 3]
        if op == VLD: r[a] = inp[b] if b < len(inp) else 0
        elif op == VXORI: r[a] ^= b
        elif op == VADDI: r[a] = (r[a] + b) & 255
        elif op == VMULI: r[a] = (r[a] * b) & 255
        elif op == VROL: r[a] = rol(r[a], b)
        elif op == VXORR: r[a] ^= r[b]
        elif op == VADDR: r[a] = (r[a] + r[b]) & 255
        elif op == VCMP: res.append(r[a] == b)
        elif op == VHLT: break
    return res

p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "machine_head", "masterkey")
code = carve(open(p, "rb").read())
n = sum(code[k] == VCMP for k in range(0, len(code), 3))
flag = bytearray()
for i in range(n):
    # state chains forward, so fix prefix and test each candidate byte at position i
    hits = [c for c in range(256) if (lambda r: len(r) > i and r[i])(run(code, bytes(flag) + bytes([c]) + b"\0" * (n - i - 1)))]
    assert len(hits) == 1, (i, hits)
    flag.append(hits[0])
print("flag:", flag.decode())
