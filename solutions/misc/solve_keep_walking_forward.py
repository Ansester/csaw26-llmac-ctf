#!/usr/bin/env python3
"""keep_walking_forward solver (static analysis only; nothing from the sample is executed).

Usage: python3 solve_keep_walking_forward.py <dir containing vcheck.7z capture.pcapng vcheck.log>
Needs: py7zr pefile dnfile scapy pycryptodome (pip install py7zr pefile dnfile scapy pycryptodome)

Chain: vcheck.7z (vcheck.exe + sideloaded version.dll) -> pcap: TLS1.2 ECDHE-RSA-AES256-GCM, decrypted with the
keylog -> 78460-byte blob from resources.csaw.io -> XOR(32-byte key derived from the AD domain name
"evermore.internal") -> Donut shellcode -> Chaskey-CTR decrypt instance -> embedded ConfuserEx .NET implant ->
emulate its constants initialiser (.cctor) statically -> LZMA string heap -> embedded PowerShell -> flag.
"""
import sys, os, re, struct, hmac, hashlib, lzma, tempfile, zipfile
import py7zr, pefile, dnfile
from scapy.all import rdpcap, TCP, IP, DNS
from Crypto.Cipher import AES

M = 0xffffffff
d = sys.argv[1] if len(sys.argv) > 1 else '.'
work = tempfile.mkdtemp(prefix='kwf_')

# ---------- 1. artifacts ------------------------------------------------------------------------
py7zr.SevenZipFile(os.path.join(d, 'vcheck.7z')).extractall(work)
print('[1] extracted:', sorted(os.listdir(work)))

# ---------- 2. pcap: reassemble TCP, decrypt TLS 1.2 (c030) with the keylog ------------------------
pk = rdpcap(os.path.join(d, 'capture.pcapng'))
streams = {}
for x in pk:
    if TCP in x and IP in x and bytes(x[TCP].payload):
        streams.setdefault((x[IP].src, x[TCP].sport, x[IP].dst, x[TCP].dport), []).append((x[TCP].seq, bytes(x[TCP].payload)))
def reasm(l):
    dd = dict(l); cur = min(dd); out = b''
    while cur in dd: out += dd[cur]; cur += len(dd[cur])
    return out
streams = {k: reasm(v) for k, v in streams.items()}
keylog = {}
for ln in open(os.path.join(d, 'vcheck.log')):
    a = ln.split()
    if len(a) == 3: keylog[a[1]] = bytes.fromhex(a[2])
def records(b):
    i = 0
    while i + 5 <= len(b):
        n = struct.unpack('>H', b[i+3:i+5])[0]; yield b[i], b[i+1:i+3], b[i+5:i+5+n]; i += 5 + n
def hello(b, typ):
    for t, v, p in records(b):
        if t == 22 and p[0] == typ: return p
def prf384(secret, label, seed, n):
    seed = label + seed; a = seed; out = b''
    while len(out) < n:
        a = hmac.new(secret, a, hashlib.sha384).digest(); out += hmac.new(secret, a + seed, hashlib.sha384).digest()
    return out[:n]
blob = None; fqdn = None
for x in pk:
    if DNS in x and x[DNS].qr == 0 and x[DNS].qd and x[DNS].qd.qtype == 6 and fqdn is None:
        fqdn = x[DNS].qd.qname.decode().rstrip('.')
for (s, sp, dst, dp), cli in streams.items():
    srv = streams.get((dst, dp, s, sp))
    if not srv or dp != 443: continue
    ch, sh = hello(cli, 1), hello(srv, 2)
    cr, sr = ch[6:38], sh[6:38]
    suite = sh[39 + sh[38]:41 + sh[38]]
    if suite != b'\xc0\x30' or cr.hex() not in keylog: continue
    kb = prf384(keylog[cr.hex()], b'key expansion', sr + cr, 72)
    skey, siv = kb[32:64], kb[68:72]
    seq = 0; ccs = False; body = b''
    for t, v, p in records(srv):
        if t == 20: ccs = True; continue
        if ccs and t in (22, 23):
            c = AES.new(skey, AES.MODE_GCM, nonce=siv + p[:8])
            c.update(struct.pack('>Q', seq) + bytes([t]) + v + struct.pack('>H', len(p) - 24))
            pt = c.decrypt_and_verify(p[8:-16], p[-16:])      # raises if the key/derivation is wrong
            seq += 1
            if t == 23: body += pt
    hdr, blob = body.split(b'\r\n\r\n', 1)
    print('[2] TLS decrypted; HTTP reply:', hdr.split(b'\r\n')[0].decode(), '| blob', len(blob), 'bytes')
assert blob and fqdn, 'could not recover the downloaded blob'
domain = fqdn.split('.', 1)[1]
print('[2] host FQDN from DNS:', fqdn, '-> domain', domain)

# ---------- 3. vcheck.exe: djb2-variant check on domain (seed 0x2393, *33) then key derivation ----
def djb(s, seed=0x2393):
    h = seed
    for c in s: h = (h * 33 + c) & M
    return h
exe = open(os.path.join(work, 'vcheck.exe'), 'rb').read()
assert struct.pack('<I', djb(domain.encode())) in exe, 'domain hash is not embedded in vcheck.exe'
def stage_key(s):            # function at vcheck.exe+0x1000 (fully unrolled): k[i] = (s[i%n]*0x83) ^ k[i-1]
    n = len(s); k = [(s[0] * 0x83) & 0xff]
    for i in range(1, 32): k.append(((s[i % n] * 0x83) ^ k[-1]) & 0xff)
    return bytes(k)
key = stage_key(domain.encode())
sc = bytes(c ^ key[i & 31] for i, c in enumerate(blob))       # stage-1 loop: xor [i & 0x1f]
assert sc[0] == 0xe8, 'not shellcode'
print('[3] decrypted shellcode, starts', sc[:5].hex())

# ---------- 4. Donut instance: Chaskey-16 CTR over everything after the 0x23c-byte header ---------
def rol(x, n): return ((x << n) | (x >> (32 - n))) & M
def chaskey(mk, blk):
    k = struct.unpack('<4I', mk); v = [a ^ b for a, b in zip(struct.unpack('<4I', blk), k)]
    for _ in range(16):
        v0, v1, v2, v3 = v
        v0 = (v0 + v1) & M; v1 = rol(v1, 5) ^ v0; v0 = rol(v0, 16)
        v2 = (v2 + v3) & M; v3 = rol(v3, 8) ^ v2
        v0 = (v0 + v3) & M; v3 = rol(v3, 13) ^ v0
        v2 = (v2 + v1) & M; v1 = rol(v1, 7) ^ v2; v2 = rol(v2, 16)
        v = [v0, v1, v2, v3]
    return struct.pack('<4I', *[a ^ b for a, b in zip(v, k)])
def ctr(mk, ctr0, data):
    c = bytearray(ctr0); out = bytearray(data)
    for p in range(0, len(data), 16):
        ks = chaskey(mk, bytes(c))
        for i in range(min(16, len(data) - p)): out[p+i] ^= ks[i]
        for i in range(15, -1, -1):
            c[i] = (c[i] + 1) & 0xff
            if c[i]: break
    return bytes(out)
inst = sc[5:5 + struct.unpack('<I', sc[5:9])[0]]
dec = inst[:0x23c] + ctr(inst[4:20], inst[20:36], inst[0x23c:])
pe_off = dec.find(b'MZ', 0x23c); asm = dec[pe_off:]
p = pefile.PE(data=asm); asm = asm[:max(s.PointerToRawData + s.SizeOfRawData for s in p.sections)]
print('[4] Donut instance decrypted; embedded .NET PE:', len(asm), 'bytes')
asm_path = os.path.join(work, 'implant.exe'); open(asm_path, 'wb').write(asm)

# ---------- 5. ConfuserEx constants: interpret <Module>::.cctor (CIL subset) up to stsfld ----------
pe = pefile.PE(asm_path); dn = dnfile.dnPE(asm_path)
md = dn.net.mdtables
m1 = md.MethodDef.rows[0]                                     # <Module>::.cctor
off = pe.get_offset_from_rva(m1.Rva); raw = pe.__data__
assert raw[off] & 3 == 3
code_size = struct.unpack_from('<I', raw, off + 4)[0]; code = raw[off + 12: off + 12 + code_size]
def rd_i32(i): return struct.unpack_from('<i', code, i)[0]
stack = []; loc = {}; pc = 0; calls = 0; steps = 0; data = None
fieldrva = {r.Field.row_index: r.Rva for r in md.FieldRva.rows}
ldc = {0x16 + i: i for i in range(9)}
while True:
    steps += 1; op = code[pc]; pc += 1
    if op in ldc: stack.append(ldc[op])
    elif op == 0x1f: stack.append(code[pc] & M if code[pc] < 128 else (code[pc] - 256) & M); pc += 1
    elif op == 0x20: stack.append(rd_i32(pc) & M); pc += 4
    elif op in (6, 7, 8, 9): stack.append(loc.get(op - 6, 0))
    elif op == 0x11: stack.append(loc.get(code[pc], 0)); pc += 1
    elif op in (0xa, 0xb, 0xc, 0xd): loc[op - 0xa] = stack.pop()
    elif op == 0x13: loc[code[pc]] = stack.pop(); pc += 1
    elif op == 0x61: b = stack.pop(); a = stack.pop(); stack.append(a ^ b)
    elif op == 0x5a: b = stack.pop(); a = stack.pop(); stack.append((a * b) & M)
    elif op == 0x58: b = stack.pop(); a = stack.pop(); stack.append((a + b) & M)
    elif op == 0x62: b = stack.pop(); a = stack.pop(); stack.append((a << (b & 31)) & M)
    elif op == 0x64: b = stack.pop(); a = stack.pop(); stack.append(a >> (b & 31))
    elif op == 0x5e: b = stack.pop(); a = stack.pop(); stack.append(a % b)
    elif op == 0x25: stack.append(stack[-1])
    elif op == 0x26: stack.pop()
    elif op == 0xd2: stack.append(stack.pop() & 0xff)
    elif op == 0x6a: v = stack.pop(); stack.append(v - (1 << 32) if v >> 31 else v)   # conv.i8 (signed)
    elif op == 0x6e: stack.append(stack.pop() & M)                                    # conv.u8
    elif op == 0x8d: n = stack.pop(); stack.append([0] * n); pc += 4
    elif op in (0x94, 0x95, 0x91): k = stack.pop(); a = stack.pop(); stack.append(a[k])
    elif op in (0x9e, 0x9c): v = stack.pop(); k = stack.pop(); a = stack.pop(); a[k] = v & (M if op == 0x9e else 0xff)
    elif op == 0x8f: k = stack.pop(); a = stack.pop(); stack.append((a, k)); pc += 4
    elif op in (0x4a, 0x4b): a, k = stack.pop(); stack.append(a[k])
    elif op == 0x54: v = stack.pop(); a, k = stack.pop(); a[k] = v & M
    elif op == 0x38: t = rd_i32(pc); pc += 4 + t
    elif op == 0x2b: t = code[pc] if code[pc] < 128 else code[pc] - 256; pc += 1 + t
    elif op == 0x2c: stack.pop(); pc += 1
    elif op == 0x32:
        t = code[pc] if code[pc] < 128 else code[pc] - 256; pc += 1
        b = stack.pop(); a = stack.pop()
        if a < b: pc += t
    elif op == 0x2f:
        t = code[pc] if code[pc] < 128 else code[pc] - 256; pc += 1
        b = stack.pop(); a = stack.pop()
        if a >= b: pc += t
    elif op == 0x45:
        n = rd_i32(pc); base = pc + 4 + 4 * n; v = stack.pop()
        pc = base + rd_i32(pc + 4 + 4 * v) if v < n else base
    elif op == 0xd0: stack.append(('fld', rd_i32(pc))); pc += 4
    elif op == 0x28:
        tok = rd_i32(pc) & 0xffffffff; pc += 4
        if tok >> 24 == 0x0a:                                    # MemberRef: RuntimeHelpers.InitializeArray
            tk = stack.pop(); arr = stack.pop(); row = tk[1] & 0xffffff
            rva = fieldrva[row]; n = len(arr)
            arr[:] = list(struct.unpack('<%dI' % n, pe.get_data(rva, 4 * n)))
        elif tok >> 24 == 0x06:                                  # MethodDef: N98 (anti-tamper, skip) / N103 (lzma)
            calls += 1
            if calls == 2: data = bytes(stack.pop()); break
    elif op == 0x00: pass
    else: raise SystemExit('unhandled opcode 0x%02x at %d' % (op, pc - 1))
assert data
props = data[0]; dsz, olen = struct.unpack('<II', data[1:9])
strings = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA1, 'lc': props % 9, 'lp': (props // 9) % 5, 'pb': props // 45, 'dict_size': dsz}]).decompress(data[9:], max_length=olen)
print('[5] ConfuserEx string heap recovered (%d bytes, %d interpreter steps)' % (len(strings), steps))
for u in re.findall(rb'(?:https?://[ -~]+|COR_ENABLE_PROFILING|System\.Management\.Automation\.Utils)', strings): print('    ', u.decode())

# ---------- 6. embedded PowerShell: rebuild the (never printed) flag variable -----------------------
ps = re.search(rb'\$__x = @\(.*?AiqwnI8wj\.log";', strings, re.S).group().decode()
def arr(name):                       # @(0x.., 0x..) assigned to a PowerShell variable (name may be ${a b})
    m = re.search(r'(?:\$|\$\{)' + re.escape(name) + r'\}?\s*=\s*@\(([^)]*)\)', ps)
    return [int(x, 16) for x in m.group(1).split(',')]
w4lk  = ''.join(map(chr, arr('__')))                          # $__  = @(...) | % {[char]$_}
b4    = ''.join(chr(x << 1) for x in arr('_x00'))             # $_x00 elements -shl 1
c4n   = re.search(r'\$2few8djdj9hc8d9ncen3n2oew9dn3nl8 = "(\w+)"', ps).group(1)[::-1]   # reversed with [-1..-len]
single = re.search(r'\$\{  \} = "(\w+)"', ps).group(1)
run5  = ''.join(chr(x + 0x10) for x in arr('___'))           # $___ | % { $_ + 0x10 }
fmt   = re.search(r'"(\{2\}\{0\}\{1\}\{3\})" -f ((?:\'\w\',? ?)+)', ps)
args  = re.findall(r"'(\w)'", fmt.group(2))
prefix = ''.join(args[int(i)] for i in re.findall(r'\{(\d)\}', fmt.group(1)))
tail  = re.search(r'\$\{      \} \+= "([^"]+)"', ps).group(1)
flag  = prefix + '{' + '_'.join([w4lk, b4, single, c4n, run5]) + tail
print('[6] flag variable (${      }) built by the script, never written to its log:')
print(flag)
