# BLOCKER: rev/music_sec_dept (unsolved)

No flag derived. Nothing here should be read as a result.

## What was established
- Shipped csirac.pd is a stub; the x86-64 external `csirac.pd_linux` builds a large Pd patch at runtime
  (a CPU emulator using session.bin as program/ROM, plus `netreceive -b 4562`). The patch text was dumped by
  running the external under vanilla Pd 0.56.2 (qemu-x86_64, host is aarch64).
- The patch uses Purr-Data-only objects `[gate N]` / `[switch N]`, which vanilla Pd cannot create.
- session.bin looks like 2-byte-instruction firmware (banner/HELP text, KEY check, encrypted flag blob).

## Why blocked
Purr-Data / pd-l2ork was never installed or run; only vanilla Pd was used. I began substituting hand-written
vanilla stand-ins for gate/switch and was told to stop, since unverified stand-in semantics could yield a wrong
or fabricated result. Nothing from that approximation is used. A real solve needs Purr-Data/pd-l2ork itself,
or a verified reimplementation of the patch's CPU.
