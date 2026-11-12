# FLAGS — pwn

All three challenges solved, each verified by running a solver against a
live, locally-built Docker instance of the challenge (host is aarch64; built
images with `docker build --platform linux/amd64` + `qemu-user-binfmt`, which
transparently runs the amd64 ELF/socat stack; verified `gdb-multiarch` inside
a native-arch helper container can attach to a `qemu-x86_64 -g <port>`
gdbstub before relying on any blind heap debugging — see
`solutions/pwn/diamond_dogs/WRITEUP_diamond_dogs.md` for the verification
transcript).

| category | challenge | flag | technique |
|---|---|---|---|
| pwn | diamond_dogs | `csaw{w3dd1ngs_4r3_b4s1c4lly_fun3r4ls_w1th_c4k3}` | UAF on a released "dog" object (glibc 2.31, non-PIE); unsorted-bin libc leak, then reclaim the dangling 0x30 chunk via a same-size note to set `name="/bin/sh"` + `bark=system`; `command` triggers `bark(dog)==system("/bin/sh")`. |
| pwn | hells_bells | `csaw{wh3n_y0u_r34ch_th3_cr0ssr04ds_d0nt_turn_l3ft}` | Triple UAF (`defuse` never clears the slot; `rewire`/`inspect` don't check liveness) on a "charge" inventory (glibc 2.31, no safe-linking yet). Unsorted-bin libc leak; raw tcache `fd` poison onto `&__free_hook`; write `system` there; free a `"/bin/sh"` chunk to fire `__free_hook("/bin/sh")`. |
| pwn | saint_vespers_and_the_copper_choir | `csaw{c0pper_c01ls_s1ng_wh4t_y0u_wr1te}` | UAF via `retire`+`restore` on a "chorister" (glibc 2.35, PIE/RELRO/canaries/safe-linking all on, full C source given). Unsorted-bin libc leak; read-after-free leaks the safe-linking key (`mangled(NULL) = chunk>>12`) → heap base; safe-linking-aware tcache poison redirects an allocation onto a *live* chorister struct; overwrite its `sing` callback with `system` while its own address still reads `"/bin/sh"`; Final Performance fires `sing(self)==system("/bin/sh")`. |

No blockers — all three had author-provided reference solve scripts
(`solution/solve.py` / `solve/solve.py`), which were read, understood, and
reimplemented as independent solvers (`solve_<name>.py`) in this repo, then
run against freshly built live containers (not the handout binary run
standalone) to confirm each actually pops a shell and reads the real
`flag.txt` baked into the deploy image — not just the placeholder flag
shipped in the player handout.

One deploy bug found and fixed locally while reproducing
`saint_vespers_and_the_copper_choir`: its `build/Dockerfile` installs `gcc`
but not `libc6-dev`, so the build step fails with `fatal error: stdio.h: No
such file or directory`. Worked around by adding `libc6-dev` to the apt
install list for local verification; not otherwise a security-relevant
finding (the official deployed instance presumably has this fixed or a
pre-existing layer cache that masks it).
