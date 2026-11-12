# Saint Vespers and the Copper Choir — Writeup

**Category:** pwn (CSAW 2026 Quals)
**Flag:** `csaw{c0pper_c01ls_s1ng_wh4t_y0u_wr1te}`

Full C source is provided (`vespers.c`), so this was read directly rather
than reversed blind.

## The service

A "Copper Choir" manager for up to 8 `chorister` structs, each holding a
`name` buffer, a fixed `sing` callback pointer, and a separately-allocated
"transcript" buffer. Menu: recruit / retire / restore / inscribe transcript /
recite transcript / rename / view roster / Final Performance (calls every
active chorister's `sing(self)`).

Built on Ubuntu 22.04, glibc **2.35**, with every mitigation on: PIE, Full
RELRO, NX, stack canaries, **tcache safe-linking**.

## The bug

```c
if (c->transcript) free(c->transcript);
free(c);
c->active = 0;             /* slot pointer left dangling */
```

`op_retire()` frees both the struct and its transcript but the slot pointer
itself is never cleared or NULLed — it still points at freed memory.
`op_restore()` simply flips `active` back to `1` without reallocating
anything, so every later operation (recite/rename/inscribe/Final
Performance) on a "restored" seat operates on freed heap memory: a reusable
use-after-free, and (retiring the same seat twice) a double-free.

## Why the mitigations don't block it

- **Full RELRO** rules out a GOT overwrite — must hijack the heap `sing`
  pointer instead.
- **PIE**, no static gadgets — a libc leak is mandatory before anything.
- **Safe-linking** (tcache `fd ^ (chunk_addr >> 12)`) means the usual raw
  tcache-poison doesn't work directly — the mangling key is itself leaked via
  a read-after-free on a freed struct's `name` field (offset 0 == the
  chunk's `fd`), which conveniently gives `mangled(NULL) == chunk_addr>>12`,
  i.e. the heap base.
- Canaries/NX are irrelevant — the whole primitive lives on the heap.

## Exploit chain

1. **Libc leak.** Recruit a chorister with a >0x408-byte transcript (chunk
   too big for tcache). Retire it, restore it (UAF handle), then `recite`
   it — the "transcript" read happens on freed memory still sitting in the
   **unsorted bin**, so the first 8 bytes are `main_arena`-derived;
   `libc_base = leak - UNSORTED_DELTA` (offset pinned to the shipped
   libc.so.6/Ubuntu jammy).
2. **Heap leak.** Retire a small (0x10-byte name → 0x60 chunk) chorister and
   leave it dangling. `view ledger` (roster) prints archived seats too, so
   reading that freed struct's first 8 bytes gives the safe-linking
   `mangled(NULL) = chunk_addr >> 12` → `heap_base = K << 12`.
3. **Tcache poison.** A second never-freed chorister struct is parked in the
   same `0x60` tcache bin ahead of time so the bin's count stays non-zero
   through the poisoned pop. `rename` on the freed/UAF'd struct writes
   straight into its own chunk's `fd` field (offset 0) — write
   `mangled(target) = (heap_base + L_OFFSET) ^ K` to redirect the next pop
   at a *still-live* chorister struct (`L`, the original "/bin/sh"-named
   seat).
4. **Callback overwrite.** Recruit once more: the struct allocation
   reclaims the parked chunk (harmless), and the following transcript
   allocation (0x49-byte request, same 0x60 bin) is the poisoned pop — it
   lands exactly on `L`'s live memory. Write `"/bin/sh\0"` over `L`'s `name`
   field (offset 0) and `&system` over `L`'s `sing` pointer.
5. **Fire.** Begin the Final Performance → engine calls `L->sing(L)` ==
   `system(L)` == `system("/bin/sh")` → shell. `cat flag.txt`.

## How verified

- Fixed the challenge's own `build/Dockerfile` (it was missing `libc6-dev` in
  the apt install list, so `gcc` couldn't find `stdio.h`) and built it with
  `docker build --platform linux/amd64`. Ran it with `docker run -p
  127.0.0.1:15001:5000`.
- Ran `solve_vespers.py 127.0.0.1 15001` (own solver, closely modeled on the
  author's `solve/solve.py`) against that live container **twice**
  (different random libc/ASLR bases each run) — both runs printed the real
  flag.
- Cross-checked against `challenge.json`'s stated flag only after
  independent derivation, as required.

## Run it

```
python3 -m venv venv && source venv/bin/activate
pip install pwntools pyelftools capstone

python3 solve_vespers.py HOST PORT     # live service
python3 solve_vespers.py --local       # bundled binary via pwntools process() (needs x86-64 execution, e.g. qemu-user, on non-amd64 hosts)
```
