#!/usr/bin/env python3
"""schrodingers_backup solver. Usage: solve_schrodingers_backup.py [evidence.zip]
Needs `cryptography`. Evidence is read in memory only (never opened by sqlite from disk).
Replays committed SQLite WAL transactions (validating salts + cumulative checksums, stopping at the
first invalid frame), XORs north^south shares at each commit where control.armed==1, derives
AES-GCM key = sha256(DOMAIN || tokens) and decrypts capsule.json."""
import hashlib, json, os, sqlite3, struct, sys, zipfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DOMAIN = b"csaw-2026/schrodingers-backup/v1\0"

def cksum(data, bo, s=(0, 0)):
    a, b = s
    for o in range(0, len(data), 8):
        a = (a + int.from_bytes(data[o:o+4], bo) + b) & 0xFFFFFFFF
        b = (b + int.from_bytes(data[o+4:o+8], bo) + a) & 0xFFFFFFFF
    return a, b

def commits(db, wal):
    ps = int.from_bytes(db[16:18], "big"); ps = 65536 if ps == 1 else ps
    magic = struct.unpack(">I", wal[:4])[0]
    bo = "little" if magic == 0x377F0682 else "big"
    assert struct.unpack(">II", wal[24:32]) == cksum(wal[:24], bo), "bad WAL header"
    seed, salts = cksum(wal[:24], bo), wal[16:24]
    pages = {i + 1: db[i*ps:(i+1)*ps] for i in range(len(db) // ps)}
    pend, fs, n = {}, 24 + ps, 0
    for off in range(32, len(wal) - fs + 1, fs):
        h, img = wal[off:off+24], wal[off+24:off+fs]
        if h[8:16] != salts: print(f"  frame {n}: salt mismatch (stale generation) -> stop"); break
        c = cksum(h[:8] + img, bo, seed)
        if c != struct.unpack(">II", h[16:24]): print(f"  frame {n}: checksum mismatch -> stop"); break
        seed = c; n += 1
        pgno, csize = struct.unpack(">II", h[:8]); pend[pgno] = img
        if csize:
            pages.update(pend); pend = {}
            yield b"".join(pages[i] for i in range(1, csize + 1))
    print(f"  {n} valid frames; {len(pend)} uncommitted page(s) discarded")

def token(snap):
    snap = snap[:18] + b"\x01\x01" + snap[20:]   # rollback-mode copy so sqlite doesn't look for a WAL
    con = sqlite3.connect(":memory:"); con.deserialize(snap)
    armed = con.execute("select armed from control").fetchone()[0]
    n = con.execute("select share from north").fetchone()[0]; s = con.execute("select share from south").fetchone()[0]
    con.close()
    return bytes(x ^ y for x, y in zip(n, s)) if armed else None

def main():
    arc = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "schrodingers_evidence.zip")
    z = zipfile.ZipFile(arc)
    db, wal, cap = z.read("catalog.db"), z.read("catalog.db-wal"), json.loads(z.read("capsule.json"))
    snaps = list(commits(db, wal))
    toks = [t for t in map(token, snaps) if t is not None]
    print(f"{len(snaps)} committed snapshots, {len(toks)} armed visits")
    key = hashlib.sha256(DOMAIN + b"".join(toks)).digest()
    print("FLAG:", AESGCM(key).decrypt(bytes.fromhex(cap["nonce"]), bytes.fromhex(cap["ciphertext"]), DOMAIN).decode())
main()
