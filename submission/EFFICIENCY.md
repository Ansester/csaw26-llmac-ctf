# Efficiency report — tokens & wall-time

**Method.** "Exact" figures are taken from the Workflow tool's own completion
telemetry (`/workflows` logs and the workflow completion notifications:
`subagent_tokens`, `duration_ms`, `agent_count`, `tool_uses`). Per-agent token/
time figures for the final verification workflow are from those logs. Figures
marked **(est.)** are approximations: the per-category autonomous solving sessions
ran in detached tmux panes whose token meters were not captured on this side, so
they are estimated from gzipped transcript size as a rough proxy and should not be
read as exact. Durations that overlap (parallel agents/tracks) do not sum to
wall-clock.

## Final verification workflow "v4" (rev + misc) — EXACT

Run `wf_d74193e1-79f`. Totals: **1,187,206 subagent output tokens**,
**wall-clock 2h16m39s** (8,198,667 ms), 6 agents (6 done, 0 errors), 318 tool
uses.

| agent | output tokens | wall-time | outcome |
|---|---|---|---|
| `rev:engine-inversion` | 347.6k | 1h12m | engine reconstructed + 9a3f decoy validated; reported flag *not uniquely determinable* (blocked) |
| `rev:live-confirm` | 282.3k | 52m45s | rebuilt engine from the decrypted patch, reproduced 9a3f decoy byte-for-byte; same "underdetermined" conclusion |
| `misc:locate` | 108.6k | 9m12s | localized the 7–8 bursts (25.17–32.47 s, R channel) |
| `misc:decode` | 236.9k | 34m57s | ring-mod/shift characterization; frag4 not recovered |
| `rev:verify` + `misc:verify` (combined) | 211.8k *(derived: total − the four above)* | — | adversarial verification |

Note: the two rev agents here independently **confirmed the engine** (a 4th
corroboration of the committed solve) but stopped short of the flag because they
treated the EXPORT argument as secret; see `solutions/rev/music_sec_dept/WRITEUP_music_sec_dept.md`.

## Superseded exploratory workflows — estimate

Four earlier workflow runs were launched and **stopped early** when human
course-corrections redirected the approach (ELF-disassembly → patch-graph →
run-the-patch → known-prefix inversion). They exist under
`…/subagents/workflows/`: `wf_de5c1733-165`, `wf_69f0ab0e-736`,
`wf_1de460aa-b8f`, `wf_8eae1379-a5c`. Their agents were cancelled mid-flight, so
no clean per-run totals were recorded. **(est.)** combined on the order of
~1–2M additional output tokens across these redirects; exact figures not
recoverable.

## Per-category autonomous solving sessions — estimate (transcript-size proxy)

Six detached Claude Code sessions (one tmux pane per category) solved their
categories. Token meters were not captured on the orchestration side; the figures
below are **(est.)** from gzipped transcript size (`submission/transcripts/`),
which correlates loosely with token volume. The larger misc/rev/web transcripts
reflect the hard, re-attempted challenges (`12345678`, `music_sec_dept`, and the
6-challenge web set), not proportional success.

| category (transcript) | gz size | relative effort (est.) |
|---|---|---|
| misc (`e8319214`, `408d5b67`, `0e07121a`) | 6.3M + 3.1M + 1.7M | high (12345678 re-attempts) |
| web (`113c6bc7`, `4ce97508`, `a23658e3`) | 3.7M + 1.9M + 0.4M | high (6 challenges) |
| rev (`4ab23db4`, `3a73e524`) | 2.7M + 0.4M | high (music_sec_dept) |
| crypto (`2235af97`) | 1.5M | medium |
| pwn (`8500a4c9`) | 0.4M | medium |
| forensics (`174d8778`) | 0.3M | low–medium |
| orchestration/HITL (`a9a173db`, `8bd4de6c`) | 0.2M + 0.1M | coordination |

## Headline

- Genuine verification of the single hardest remaining challenge
  (`rev/music_sec_dept`) cost **~1.19M tokens / 2h17m** of multi-agent work in the
  final pass — and still returned an honest "underdetermined" from the from-scratch
  agents; the committed solve came from an externally-supplied derivation that was
  then **reproduced and cross-checked here** against the real artifacts.
- The genuine-solve discipline (adversarial verifiers re-running candidate scripts;
  rejecting hardcoded/back-fit answers) is the main token cost multiplier, and the
  main reason no wrong flag was submitted.
