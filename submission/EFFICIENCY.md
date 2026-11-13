# Efficiency report

## How these numbers were produced (so they're reproducible)
Parsed every committed transcript (`transcripts/*.jsonl.gz`) and every workflow agent log
(`transcripts/solved/workflows/*/*.jsonl`), read each assistant message's reported
`usage`, and **deduplicated by message id (keeping the maximum output per id)** so
streamed/re-emitted copies aren't counted twice. The script is in our notes; anyone can
re-run it over the committed logs and get the same totals.

Two honest caveats:
- **Output tokens are the clean metric.** Each assistant message has a unique id, so the
  output total is not inflated by shared context.
- **Input is reported separately and is an upper bound.** It sums `input_tokens` +
  `cache_read` + `cache_creation`, which is dominated by **prompt-cache reads** and by
  history that is **inherited/shared across sessions** (e.g. orchestration history replayed
  into a category session). So the input figure massively over-counts distinct input and
  should be read as "context volume processed," not "unique input."

## Totals (all sessions + all workflow agents)
| metric | value |
|---|---|
| Model **output** tokens (deduped) | **≈ 2.62 million** (2,622,726) |
| Input + cache tokens (upper bound, cache-inflated) | ≈ 378 million |
| Distinct models used | `claude-opus-5-5`, `claude-opus-4-8`, `claude-sonnet-5-5`, `claude-sonnet-5` (Claude Code agents) + ChatGPT (2nd LLM, one challenge) |

(A `<synthetic>` marker also appears in the logs — that is a harness-injected synthetic
record, not a model, and is excluded from "models used".)

## By work group (output tokens / input+cache)
| group | output tokens | input+cache (upper bound) |
|---|---|---|
| multi-agent workflows (the 2 hardest challenges) | 1,517,420 | 112.0 M |
| web (6 challenges) | 320,162 | 140.4 M |
| rev (3) | 269,952 | 33.6 M |
| orchestration / HITL (main) | 253,422 | 31.2 M |
| misc (3) | 170,023 | 43.3 M |
| pwn (3) | 33,395 | 7.5 M |
| crypto (4) | 29,765 | 5.6 M |
| forensics (4) | 23,738 | 3.5 M |
| orchestration (misc VM sessions) | 4,849 | 0.7 M |

**What this shows:** the "easy" categories were cheap (crypto/forensics/pwn each under ~35k
output tokens for all their challenges). Cost concentrated in (a) the two hardest
challenges' multi-agent workflows (~1.5M output — the adversarial verify fan-out is the
expensive part), (b) web (six challenges, several with live services), and (c) the
human-in-the-loop orchestration.

## Wall-clock (where recorded)
Per-challenge wall-time isn't cleanly separable because each category ran as one continuous
session over multiple challenges, with overnight idle gaps. Recorded spans we can cite:
- The final multi-agent workflow (`ctf-final-two`, covering rev/music_sec_dept **and** the
  blocked audio challenge jointly): **≈ 2 h 16 m**, with per-agent spans of
  rev:engine-inversion ≈ 1 h 12 m, rev:live-confirm ≈ 52 m, misc:decode ≈ 35 m,
  misc:locate ≈ 9 m.
- Overall effort spanned ~2 calendar days (start to submission) including two interruptions
  (an out-of-memory crash and an overnight VM reboot), both recovered with ~no lost work
  because every agent committed continuously.

## Per-challenge attribution (limitation, stated plainly)
We do **not** publish a precise per-challenge token number: the category sessions each
solved several challenges in one log, and the final workflow worked on rev **and** the
blocked audio challenge together, so attributing its 1.5M output tokens to a single
challenge would be wrong. Category-level output tokens above are the honest granularity the
logs support.
