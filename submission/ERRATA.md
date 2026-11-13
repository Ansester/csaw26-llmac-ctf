# Errata & known limitations (2026-11-13)

A post-submission self-review found issues in the submitted code, evidence, and
metrics. We record them here rather than silently rewriting the competition evidence.
The original solver code and transcripts are left intact; corrected statements live in
this file and in `DISCLOSURE.md`.

## Solver code defects (in the submitted, competition-time code — not patched in place)
- **flagchecker — no acceptance gate.** `framework/solutions/web/solve_flagchecker.py`
  discards the HTTP response and catches all exceptions, so a failed request becomes a
  timing sample; it prints `FLAG` on reaching `}` or 80 chars without checking the
  service returned `{"correct": true}`. An in-memory check with a server that always
  returns `correct:false` still made it print `csaw{}`. The live run's confidence came
  from the separate `.env` comparison in `run_flagchecker_in_vm.sh`, not from an
  in-script acceptance check. PRESENTATION's "confirmed against the response" wording
  overstates the script; treat the `.env` match as the verification mechanism.
- **flagchecker — stale-candidate ranking.** Later sampling rounds only re-sample the
  surviving pool but rank over the full candidate dict, so an eliminated character can
  win on a stale, higher noisy minimum. Demonstrated deterministically in memory.
- **flagchecker wrapper.** `run_flagchecker_in_vm.sh` does not propagate pipeline
  failure, exits 0 on a flag mismatch, force-removes a fixed container name, and assumes
  port 5055/`sleep 6` readiness; it is GNU/Linux-specific (`sed -i`). VM/Linux only.
- **pwn `--local`.** The three pwn solvers use `process(BIN)` and bundled-libc offsets
  but do not launch via the bundled loader or select that libc, and need a local flag
  fixture; local mode is only meaningful in a matching Linux/amd64 environment.
- **music runner portability.** `emulator.py`/`native_batch_verify.py` fall back to a
  hardcoded `/Users/ashmit/Desktop/...` path and a macOS Purr-Data binary;
  `native_batch_verify.py` treats the presence of "rendering stem" as success rather
  than a full render+comparison. `run.py`/`solve.py` overwrite their evidence files on
  rerun. Set `CSIRAC_ARTIFACTS` and treat the committed outputs as the record of record.

## Missing inputs and source (not bundled)
- **Challenge inputs absent**: `session.bin`, `csirac.pd_linux`, `hidden_patch.pd`
  (music_sec_dept), `12345678 (1).wav` (audio), `keep_walking_forward`'s pcap/7z/log,
  and the service challenges' source/Docker/compose are not committed. Solvers assume a
  pre-existing challenge checkout. `reextracted_patch.pd` is a patch *derived from the
  ELF*, not the original ROM/ELF. Reproduction requires the upstream DB
  (`NYU-LLM-CTF/CSAW26_LLMAC_DB`, `2026/CSAW-Quals/`); the archived clone commands used
  `--depth 1` with no pinned commit, so the exact artifact revision is not fixed here.
- **Custom workflow source absent.** `framework/` has prompts, solvers, and workflow
  *trajectories*, but not the workflow scripts themselves. The real trajectory
  (`transcripts/solved/rev__4ab23db4.jsonl.gz`) invokes `Workflow` with a `scriptPath`
  ending `workflows/scripts/ctf-final-two-v4-wf_8eae1379-a5c.js`; that file lived in the
  VM session directory and is not committed. The orchestration used Claude Code and its
  built-in Workflow facility (external tooling), not a from-scratch framework.

## Metrics (`report/EFFICIENCY.md`) need a defined source
The 1,187,206-token figure is not tied to a cited completion record. The logs do carry
`message.usage`/IDs/timestamps, but sessions share inherited history (64 shared UUIDs
between one orchestration and one rev log), repeated message blocks, and the final
workflow spans *both* rev and the blocked audio challenge — so whole-session sums
double-count and a single-challenge attribution is not supported. Any token total
should state whether it is input/output/cached and how duplicates were handled; gzip
size is not a token proxy.

## Stale or overstated technical claims (corrected statements)
- **music_sec_dept KEY**: the firmware's KEY handler is a lenient byte parser (six hex
  pairs → six key bytes), not a password compare. The "13-char `M4ch1n3_K3y!!` decoy vs
  12-char real" line was an early hypothesis, not a settled fact; the recovered key is
  `bf03942fbd12`. The final solve fixes a 10-char EXPORT argument and uses a readability
  ranking over 87 candidates — it is **not** constrained by the public prefix/suffix
  alone. A faithful interpreter rendering a chosen key establishes faithful execution,
  not a uniqueness/correctness oracle.
- **saint_vespers**: the writeup says a never-freed struct is parked in tcache, but
  `solve_vespers.py` retires/frees the spare chunk. The exploit relies on a particular
  allocation layout, not a generally proven heap base.
- **golf_heist**: the referenced `GHSA-...` identifier is a GitHub advisory, not a CVE.
- **juggler**: the "booleans being airborne" metaphor is flavor; the real mechanism is
  PHP mass-assignment + loose (`==`) comparison.
- **12345678 blocker**: "no hardcoded constants" means no hardcoded *answer fragments* —
  the solver does contain fixed windows/frequencies/thresholds/font tables. The
  ring-modulation diagnosis is a hypothesis; "ASR fails by design"/"exhaustive" are
  stronger than finite failed attempts establish. The metadata flag quoted in the
  blocker is unsubmitted ground truth, not a claimed solve.

## Environment / dependencies (not pinned)
No `requirements.txt`/Dockerfile is tracked. Solvers need, variously: `requests`,
`pycryptodome`, `pwntools`, `Pillow`, `cryptography`, `PyJWT`, `imageio-ffmpeg`,
`py7zr`, `pefile`, `dnfile`, `scapy`, `numpy`, `scipy`, `faster-whisper` (+ ASR model
assets). `solve_schrodingers_backup.py` needs a Python/SQLite with
`sqlite3.Connection.deserialize`. Model identifiers actually present in the logs:
`claude-opus-5-5`, `claude-opus-4-8`, `claude-sonnet-5-5`, `claude-sonnet-5` (Claude
Code agents) and ChatGPT (exact model not recorded in the export).
