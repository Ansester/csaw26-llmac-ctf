# BLOCKER: rev/music_sec_dept (unsolved -- substantial progress, no flag)

No flag derived. Nothing here should be read as a result. This supersedes the
previous (stale, pre-Purr-Data) version of this file.

## Architecture established
- `csirac.pd_linux` (x86_64 Rust Pd external) decrypts and `binbuf_eval`s a
  ~123 KB Pd patch at load time; the decoded text is `rev/scratch_music_sec_dept/hidden_patch.pd`
  (RE scratch artifact, not a deliverable -- deleted from this branch, see commit).
- `session.bin` (4284 bytes) is loaded into two Pd arrays, **`pb`** (256
  entries) and **`kb`** (3972 entries), each storing **(opcode, operand)
  float pairs** -- i.e. `session.bin` is 2-byte-instruction firmware for a
  bytecode VM implemented by the rest of the patch (register ops `reg_a..d`,
  `inc`/`dec`, numeric `route 0 1 2 6 7` opcode dispatch, etc).
- Reading `kb` back out (as raw 32-bit float samples via `[soundfiler write
  -bytes 4 ...]`, decoding opcode `128`/`129` pairs as "emit literal char")
  reconstructs the **entire ROM string table** verbatim, independent of
  whether the VM has ever been clocked: the full banner, HELP text, the
  CUE/SYNC/EQ/KEY/DECK/EXPORT/RECALL help lines, every status and error
  string (`decks 1-6 loaded`, `beatsync enabled`, `filter set`, `keymatching
  enabled`, `ARMED`, `rendering stem ...`, `? invalid argument ;_;`, `? deck
  locked: keymatching error. EJECT and restart.`, `? stem already bounced`,
  `USB ejected. good night <3`, etc), and the full crate/deck table
  (`41 LONDON_SONG`, `45 IPOD_TOUCH`, `49 FSCK_MY_COMPUTER`, `4b CSIRAC`,
  `4f DELETE`, `53 =^..^=`, `57 ALL_I_AM`, `5b INFOHAZARD`,
  `5f BATTERY_DEATH`, `63 SING_GOOD`, `67 ITS_YOU`, `6b ALL_AT_ONCE`).
- `pb` additionally contains, verbatim, the **DENIED decoy**: a `KEY > `
  prompt echo followed by `DENIED` and then a literal `flag{` ... garbled
  bytes ... `}` -- this is the fake/trap flag a wrong `KEY` is meant to
  produce; **never submit it** (consistent with the task's stated
  decoy-flag policy). It stayed byte-identical before and after sending a
  full correct command sequence over the console, confirming it is static
  ROM content, not a live render.
- None of `pb`/`kb`/`hcurs`/`cuemark`/`pmark` ever contain a `csaw{` string
  at rest (checked again this session) -- the real flag, if produced, is
  rendered transiently (e.g. streamed out over the TCP console, or into a
  DSP/audio buffer for the "stem"), not parked in a static array.

## Headless clock: solved this session
The VM only advances when something bangs the chain that the GUI's `[tgl
Run]` button drives (inside the dynamically-built patch's `hz` subpatch):
`metro 100` (10 Hz, matching the task's documented default) -> on each tick,
three **global** messages fire: `; cuec execute ;`, `; headc step ;`,
`; headc out ;`. Because Pd message-box `; name ... ;` syntax addresses a
GLOBAL receiver (`[r cuec]`, `[r headc]` exist deep in the dynamically-built
patch), a **separate, independently-authored** `.pd` file opened in the same
Pd process can drive the exact same global receivers without touching the
dynamically-generated patch at all. Built `vm_control4.pd` (committed in this
folder in support of this note's claims) with `[netreceive -b 5555]` on a
spare port: a single raw byte `1` starts a local `metro 100` wired to the
same three global sends, byte `0` stops it, byte `3` triggers `[soundfiler
write -bytes 4 ...]` dumps of `pb`/`kb`/`hcurs`/`cuemark`/`pmark` to
`/tmp/dump_*.wav` for inspection from the host via `docker cp`.
Launch: `purr-data -nogui -nodac -noadc -stderr -path <dir> -open
<dir>/csirac.pd -open <dir>/vm_control4.pd -send 'pd dsp 1'`.
**Caveat found the hard way:** a *non-binary* (FUDI-parsing) `[netreceive]`
in this specific Purr-Data 2.20.1 / qemu-x86_64 build reliably **aborts the
whole Pd process (`Pd: signal 6`)** on receiving any text message, with or
without a client disconnect. Only `-b` (raw byte) netreceive survives, so the
control channel and all byte-level framing must use `-b`.

## Confirmed (once, not yet reliably reproduced): the console IS two-way
With the injected clock running, opening a **fresh** TCP connection to
4562, sending `DECK` and reading the same socket for a few seconds returned
literal `b' decks 1-6 loaded\n'`, and a later run returned `b'\nCSIRAC> '`
and `b' filter set\n'` -- i.e. the live VM genuinely answers over the same
raw-byte netreceive port, with real ROM strings, not an echo. This is the
single most important finding: the console protocol described in the task
(`CUE ... -> decks 1-6 loaded`, etc.) is real and reachable headless.

## Why still blocked
Reproducing that live exchange on demand failed on every subsequent clean
attempt (full container restart, clock armed first, single connection, long
per-command waits up to 15s and a 150s patient single-command wait): zero
bytes back. The successful reads above came from a long-lived container that
had accumulated several hours of prior interaction (visible in leftover
`/root/*.log` files from an earlier session not captured in this repo), so
the output we saw may have been a backlog flushing to a newly-connecting
client rather than a direct reply to our own command -- i.e. **response
timing/ordering relative to our injected clock is not understood well enough
yet** to reliably drive `KEY`/`DECK`/`EXPORT`/`RECALL` and capture their
replies in sequence. Given qemu-x86_64 user-mode emulation of the Rust
external on this (non-x86_64) host, each VM "tick" may cost much more wall
time than the nominal 100 ms metro period, and the console's framing bytes
(`route 253 254` / `sel 255` seen in the patch's own TCP-receive subpatch)
may matter for getting clean, non-interleaved per-command input, which this
session's plain LF-only sends did not account for.

## Not reached this session
- Capturing a real `EXPORT 9a3f` reply (or any reply) reliably enough to
  compare against the task's documented decoy render
  (`L7USw*KLz'0VI/3)keO#]_}z":M$tYIFf-HB'c8NwU`) or to look for `csaw{`.
- Ghidra decompilation of `csirac.pd_linux`'s xorshift-PRNG string
  deobfuscator / EXPORT seed transform (not attempted this session; the
  live-protocol path above looked more promising once two-way I/O was
  confirmed, so effort went there first).

## Repro
`vm_control4.pd` in this folder + the launch command above reproduce the
clock injection and array dumps. `solutions/rev/music_sec_dept/console_probe.py`
in this folder is the exact script used for the one successful exchange and
the later unsuccessful attempts; rerun it against a longer-lived container
(or just keep retrying with longer waits) to try to reproduce reliably.
