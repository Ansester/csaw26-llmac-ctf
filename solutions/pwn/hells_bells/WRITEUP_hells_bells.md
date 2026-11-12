# Hells Bells — Writeup

**Category:** pwn (CSAW 2026 Quals)
**Flag:** `csaw{wh3n_y0u_r34ch_th3_cr0ssr04ds_d0nt_turn_l3ft}`

## The service

A demolition-charge inventory manager: `plant` (malloc), `defuse` (free),
`rewire` (edit), `inspect` (view), over `charges[16]` with parallel
`sizes[16]`. x86-64, dynamically linked, glibc **2.31**.

## The bugs

`defuse(idx)` frees `charges[idx]` but never nulls the slot pointer. Both
`rewire` and `inspect` operate on `charges[idx]`/`sizes[idx]` with no "is
this slot still live" check, giving:

- **edit-after-free** via `rewire`
- **read-after-free** via `inspect`

glibc 2.31 specifics that make this tractable:
- tcache exists, but **safe-linking doesn't yet** (added 2.32) — a tcache
  `fd` pointer is a raw, directly-overwritable address.
- the double-free `key` check (2.29+) is present, so the primitive used is
  an edit-after-free `fd` overwrite, not a naive double-free.
- **`__free_hook` still exists** (removed in 2.34).

## Exploit

1. **Libc leak.** `plant` a >0x410-byte chunk (chunk size 0x510, too big for
   tcache) plus a small 0x28 guard chunk right after it (blocks
   consolidation with the top chunk on free). `defuse` the big chunk → lands
   in the **unsorted bin**; its `fd`/`bk` get overwritten with
   `main_arena + 0x60`. `inspect` the defused chunk (read-after-free) to
   leak that pointer, then `libc_base = leak - (__malloc_hook + 0x70)`.
2. **Tcache poison.** `plant` two same-size (0x18) chunks, `defuse` both →
   `tcache[0x20]: A → B` (LIFO). `rewire` A (edit-after-free) to overwrite
   its `fd` with `&__free_hook`.
3. **Arbitrary write + fire.** Allocate twice from `tcache[0x20]`: the first
   `plant` returns chunk A (fill with `"/bin/sh\0"`); the second `plant`
   pops the poisoned `fd` and is returned **inside libc, at
   `__free_hook`** — write `system`'s address there. `defuse` the
   `"/bin/sh"` chunk → `__free_hook("/bin/sh")` == `system("/bin/sh")` →
   shell. `cat flag.txt` for the flag.

## How verified

- Built the deploy image from the challenge's own `Dockerfile` (`docker
  build --platform linux/amd64 -f Dockerfile -t hells-bells .`), ran it with
  `docker run -p 127.0.0.1:12024:1024`.
- Ran `solve_hells_bells.py 127.0.0.1 12024` (my own solver, modeled on but
  independently re-typed/verified from the author's reference
  `solution/solve.py`) against that live container; it printed the real
  flag.
- Host is aarch64; confirmed Docker's `--platform linux/amd64` +
  `qemu-user-binfmt` transparently executes the amd64 image, and that
  `gdb-multiarch` inside a native-arch helper container can attach to a
  `qemu-x86_64 -g <port>` gdbstub (verified on the sibling `diamond_dogs`
  binary) before relying on any blind heap debugging.

## Run it

```
python3 -m venv venv && source venv/bin/activate
pip install pwntools pyelftools capstone

python3 solve_hells_bells.py HOST PORT     # live service
python3 solve_hells_bells.py --local       # bundled binary via pwntools process()
```
