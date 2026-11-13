music_sec_dept — artifact-derived recovery and native interpreter verification

Run with Python 3.8+ (standard library only):
    python3 run.py

The script re-extracts hidden_patch.pd from the original ELF, verifies it against
the patch used for VM reconstruction, reproduces the complete independent
42-character checkpoint, derives all 12,288 states satisfying public csaw{
syntax, keeps all 87 closing-brace candidates, ranks by a generic character
preference, derives each corresponding KEY, and replays the selected candidate
through the full VM. The flag body and recovered KEY are not solver inputs.
There is no metadata flag read and no target-body comparison.

Native verification:
native_runs/repaired_checkpoint and native_runs/independently_recovered contain
actual Purr-Data interpreter output, generated transport/controller patches and
source hashes. Both the full checkpoint and recovered flag were emitted by the
original patch computation and original ROM.

The environment forbids listening sockets. Consequently ONE network object
was replaced by local_transport, preserving the original raw-byte input queue
and output byte path. A separate controller supplies complete LF command lines
only after the exact prompt and drives headc out, headc step, cuec execute in
the original order. ROM and cipher logic were unchanged. The native processes
were stopped after the complete response was captured; original logs are kept.
This is artifact execution evidence, not competition-server acceptance.

Argument length is derived from firmware queue-length reads: the four leading
characters are literal bytes; six additional filler characters change the
queue-length-dependent state. Their content is drained and immaterial for the
tested inputs. The six dots in ROM RECALL supply an artifact-grounded initial
choice. Native replay used these dots, not a copied published argument.

Provenance:
The coordinating conversation had already encountered public solution material.
The independent recovery worker received neither the solution KEY nor flag body,
consulted only local artifacts and prior artifact-derived mechanism findings,
and implemented its own VM. Preserve this disclosure with the complete record;
do not claim that the entire conversation was never externally exposed.

Audio challenge status: unresolved fourth fragment. No audio flag is claimed.
