# Diamond Dogs — Writeup

**Category:** pwn (CSAW 2026 Quals)
**Flag:** `csaw{w3dd1ngs_4r3_b4s1c4lly_fun3r4ls_w1th_c4k3}`

## The service

A "K-9 unit manager" menu: adopt/command/release a dog, and file/read/shred a
note. Non-PIE x86-64 binary, glibc 2.31.

The dog object is:

```c
struct dog { char name[0x18]; void (*bark)(struct dog *); };   // 0x20 bytes -> 0x30 tcache chunk
```

`command(idx)` calls `dogs[idx]->bark(dogs[idx])` — note that the callback
receives a pointer to the **start** of the struct, i.e. to `name`.

## The bugs

1. **Use-after-free on release.** `release(idx)` frees the dog's chunk but
   never clears `dogs[idx]`, so the slot still points at the (now freed, but
   un-zeroed) memory. `command` can still be invoked on a released dog.
2. **Same-size reclaim via notes.** `file note` allocates a buffer the caller
   fully controls. Filing a 0x20-byte note after releasing a dog reclaims
   that exact tcache chunk (tcache is LIFO, same-size-class), overwriting the
   freed dog object with attacker bytes — including the `bark` function
   pointer.
3. **Read-after-free leak.** `shred note` frees a note's buffer without
   clearing the pointer; `read note` on a shredded big (>0x410, so unsorted
   bin rather than tcache) note leaks heap/libc bytes left over from the
   freelist metadata (`main_arena`-derived pointer, `fd`/`bk` of the unsorted
   bin entry).

## Exploit

1. **Libc leak.** File a 0x500-byte note (too big for tcache, goes to the
   unsorted bin on free) and a small 0x28 guard note so the big chunk doesn't
   consolidate into top. Shred the big note, then read it back — the first
   8 bytes are `main_arena + 0x60` (glibc 2.31 unsorted-bin bookkeeping),
   from which `libc_base = leak - (__malloc_hook + 0x70)`.
2. **UAF reclaim.** Adopt a dog (one 0x30 chunk) and release it →
   `tcache[0x30]`, with `dogs[0]` still pointing at the freed chunk. File a
   0x20-byte note that reclaims that exact chunk: `name = "/bin/sh\0..."`,
   `bark = system` (writing the pointer right after the 0x18-byte name
   field).
3. **Fire.** `command(0)` → `dogs[0]->bark(dogs[0])` == `system(dogs[0])` ==
   `system("/bin/sh")` → shell. Send `cat flag.txt` to read the flag.

## How verified

- Built the deploy image from the challenge's own `Dockerfile` (`docker build
  --platform linux/amd64`), ran it with `docker run -p 127.0.0.1:12025:1025`.
- Ran `solve_diamond_dogs.py 127.0.0.1 12025` against that live container and
  it printed the real flag, matching `files/flag.txt`'s placeholder format
  and the challenge's documented flag (cross-checked only after independent
  derivation).
- Host is aarch64 (no native x86-64 execution); confirmed `qemu-user-binfmt`
  + Docker's `--platform linux/amd64` transparently runs the amd64 socat/ELF
  stack. Verified `gdb-multiarch` (inside a small arm64-native helper
  container with `qemu-user` + `gdb-multiarch` installed) can attach to a
  `qemu-x86_64 -g <port>` gdbstub for `guard-dog` and read registers before
  relying on it for any blind heap debugging.

## Run it

```
python3 -m venv venv && source venv/bin/activate
pip install pwntools pyelftools capstone   # or vendor as needed

python3 solve_diamond_dogs.py HOST PORT     # live service
python3 solve_diamond_dogs.py --local       # bundled binary via pwntools process() (needs matching libc/ld + x86-64 execution, e.g. qemu-user)
```
