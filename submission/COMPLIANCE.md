# Compliance checklist — requirement → where it's satisfied

A map from each competition requirement to the file(s) that satisfy it. ✓ = covered;
⚠️ = covered but with a disclosed caveat the organizers must weigh (we flag these rather
than hide them — see `DISCLOSURE.md`).

## The presentation must cover
| Required | Where |
|---|---|
| Overall approach & workflow | `report/APPROACH.md`, `report/SLIDE_DECK.pdf`, `report/SUBMISSION.md` |
| AI systems/models and how used | `report/APPROACH.md` (model choice), `report/EFFICIENCY.md` (models in logs) |
| Prompting strategy & tools | `report/APPROACH.md`; prompts in `framework/prompts/` |
| Challenges that shaped approach + lessons | `report/APPROACH.md` → "Challenges that shaped our approach" |
| Results & examples of solved challenges | `report/MANIFEST.md`, `report/FLAGS.md`, `report/writeups/`, deck deep-dives |
| 10-minute presentation (slides) | `report/SLIDE_DECK.pdf` |

## Report & submission requirements
| Required | Where / status |
|---|---|
| Per challenge: flag matches the correct flag | `report/FLAGS.md`, `report/MANIFEST.md`; metadata cross-check noted per challenge in `DISCLOSURE.md` |
| Human-readable solution process (trajectory/log/conversation) | `transcripts/` (14 session logs + `workflows/` + `external/`) |
| HITL: full conversation history + proof of flag + brief strategy | `transcripts/` (histories), `report/writeups/WRITEUP_<name>.md` (per-challenge strategy) |
| Autonomous: transcript as-is, no manual tampering | `transcripts/solved/workflows/` (committed untouched) |
| All code & data in a git repo | code: `framework/`. **⚠️ challenge input files are not bundled** — documented with the pinned upstream source in `report/ERRATA.md` |
| Final presentation report (prompting, model, tool usage) | `report/APPROACH.md` |
| How specific challenges affected agent engineering | `report/APPROACH.md` |
| Overall token usage & time cost | `report/EFFICIENCY.md` |
| Name the AI systems used | `report/APPROACH.md`, `report/EFFICIENCY.md` (Claude models + ChatGPT) |

## Rules that need an honest flag (disclosed, organizers to weigh)
| Rule | Our status |
|---|---|
| "All solution steps must come from the AI system" | ✓ in general; image/audio reads were the model's own vision; two challenges had the answer in the prompt (below) |
| **"Prompts must not contain direct solutions"** | ⚠️ **`finders_keepers`** (plaintext answer in the crypto prompt) and **`breach_zero_day`** (author solve-path + flag in a prompt); `secret_treaties` got an English flag rendering. **Fully disclosed in `DISCLOSURE.md`.** Eligibility/penalty is the organizers' decision — we do not claim these are clean. |
| **"No online write-ups/source to form the agent"** | ⚠️ **`music_sec_dept`**: our second LLM web-searched a public recipe. Disclosed; the committed derivation is answer-agnostic. |
| DB reference files allowed? | Per our understanding of an organizer clarification (primary reply not in repo). ~12 solves used DB author references; listed in `MANIFEST.md`. |

## Judging-rubric coverage
- **Challenge Solved (35%)** — 22 of 23 recovered (`MANIFEST.md`).
- **Approach (55%)** — prompting technique, solution workflow, harness/model choice
  (`report/APPROACH.md`); autonomous multi-agent framework + its trajectories
  (`transcripts/solved/workflows/`); efficiency (`report/EFFICIENCY.md`).
- **Presentation (10%)** — `report/SLIDE_DECK.pdf` (built with an LLM).
- **Per-challenge "how the LLM solved it" summary** — each `report/writeups/WRITEUP_<name>.md`.

## "A successful submission will include"
1. **All prompts & responses** — `transcripts/` + `framework/prompts/`. ✓
2. **A brief write-up of strategies** — `report/SUBMISSION.md`, `report/APPROACH.md`, and
   per-challenge `report/writeups/`. ✓

**Honest bottom line:** every structural requirement is met and located above. The two
rule-sensitive items (direct-solution-in-prompt for 2–3 challenges, and one web-search) are
disclosed openly; we leave their scoring to the organizers rather than assert compliance.
