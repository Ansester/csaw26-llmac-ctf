# CSAW 2026 Quals LLM-CTF — 10-Minute Presentation (3 speakers)

Every number here is from `MANIFEST.md` / `DISCLOSURE.md` and is defensible. The talk
leads with the **system** and our **self-audit**, not with purity claims — because the
honest account is the one that survives a judge's follow-up. Fill `[P1]/[P2]/[P3]` with
real names; the event is at 17:00 GST.

## Roles
- **P1 — System.** Opens and closes. Thesis, architecture, models/tools.
- **P2 — Method.** The genuine-solve rule, the self-audit, one clean deep dive.
- **P3 — Results & honesty.** The real breakdown, the hard multi-LLM solve, the blocker.

Rehearse the three handoffs cold. One sentence every presenter must be able to say
verbatim: **"22 of 23 recovered; we audited our own run and disclosed exactly how each
was solved — 8 with no outside help, 12 using the provided reference solutions, 2 where
the answer was already in the prompt, 1 where a second model web-searched — and we leave
eligibility to you."**

## Minute-by-minute sheet

| Time | Slide | Speaker | Beat |
|------|-------|---------|------|
| 0:00–0:40 | 1 Title | P1 | Hook + one-sentence honest thesis |
| 0:40–1:40 | 2 Approach | P1 | Hybrid autonomous + HITL + 2nd LLM; the constraints |
| 1:40–3:10 | 3 Architecture | P1 | The system: VM fan-out, orchestration, workflow |
| 3:10–4:00 | 4 The rule | P2 | Genuine-solve rule + metadata-as-cross-check |
| 4:00–5:10 | 5 Self-audit | P2 | We audited ourselves and found our own gaps (the differentiator) |
| 5:10–6:00 | 6 Deep dive: flagchecker | P2 | A clean solve, start to finish, with its honest caveat |
| 6:00–7:20 | 7 Results | P3 | The real breakdown: 8 / 12 / 2 / 1 / 1 |
| 7:20–8:30 | 8 Deep dive: music_sec_dept | P3 | Multi-LLM, web-search disclosure, answer-agnostic worker |
| 8:30–9:10 | 9 The blocker | P3 | misc/12345678 — why we submitted nothing |
| 9:10–9:50 | 10 Lessons | P1 | Meta-honesty: the audit caught our first audit's miss |
| 9:50–10:00 | — | all | Questions |

If over: P2 trims slide 6 detail, P3 compresses slide 9. If under: P3 expands the results
breakdown.

## Full script

### P1 — Opening (0:00–3:10)

**[SLIDE 1 — Title] (0:00)**
"Good evening. We ran CSAW as an experiment in two things at once: can autonomous LLM
agents cover a whole CTF, and can we be honest enough about *how* they did it that the
account survives scrutiny? We recovered 22 of 23 flags. And we audited our own run hard
enough to tell you, per challenge, exactly what help each one had. I'll show the system;
[P2] shows the discipline and how we checked ourselves; [P3] shows the real results and
the hardest solve."

**[SLIDE 2 — Approach] (0:40)**
"This was a hybrid, which the rules allow. Six autonomous Claude Code agents, one per
category, running in parallel — plus a human-in-the-loop layer that wrote the prompts
and reviewed outputs, plus a second LLM, ChatGPT, on the single hardest challenge. We
gave ourselves three constraints: everything ran on a disposable VM, nothing touched our
own machines, and it cost nothing but tokens."

**[SLIDE 3 — Architecture] (1:40)**
"The system: six Claude Code sessions in tmux on an isolated VirtualBox VM, one git
branch per category, pushing as they solved. On top, an orchestration layer authored
structured task briefs and reviewed every flag. For the two hardest challenges we
escalated to a multi-agent workflow — it fans out solver agents and ends each run with an
adversarial verifier that tries to *disprove* the finding. One detail that validates the
design: an overnight VM reboot killed all six sessions and we lost nothing, because
everything was already committed to git. [P2], over to you."

### P2 — Method & a clean solve (3:10–6:00)

**[SLIDE 4 — The rule] (3:10)**
"Every agent ran under one rule: a flag counts only if a live service accepts it, or a
script we run derives it from the challenge's own files. The flags sitting in the
metadata were cross-check only. That rule is also why we can be precise about exceptions
— we wrote it down, so we can tell you exactly where it held and where it didn't."

**[SLIDE 5 — We audited ourselves] (4:00)**
"Here's what we're actually proud of. After solving, we ran a self-audit of our own
transcripts and prompts — and it found things we'd gotten wrong. Our *first* audit said
one crypto challenge was solved clean; a deeper pass found the plaintext answer was
sitting in that challenge's own prompt. We corrected it, in writing, in our disclosure.
We'd rather hand you that than have you find it. Every exposure — reference use, an
answer in a prompt, a web search — is in `DISCLOSURE.md` and a per-challenge manifest."

**[SLIDE 6 — Deep dive: flagchecker] (5:10)**
"One clean example. A web endpoint's comparison sleeps ten milliseconds per correct
leading character — a timing oracle — armed only by a crafted browser User-Agent. The
agent recovered the flag character by character using the minimum response time, since
jitter only ever adds delay. Honest caveat, and it's in our errata: the script itself
didn't gate on the server's 'correct' response — the live confirmation came from a
separate check in the runner. We flag that rather than overstate the script. [P3] — the
real numbers."

### P3 — Results, the hard solve, the blocker (6:00–9:10)

**[SLIDE 7 — Results] (6:00)**
"22 of 23 recovered. Here's the honest breakdown, and these are the numbers we defend:
**8** challenges solved with no reference and no answer in the prompt. **12** used the
challenge database's own author reference solutions — which we understand the organizers
to permit, and which we list by name. **2** had the answer already in the prompt —
finders_keepers and breach_zero_day — we disclose both. **1**, the hardest, involved a
web search by our second model — disclosed. And **1** we did not solve. Whether each
recovery earns credit is your call; our job was to make that call possible on the
evidence, and all the trajectories are in the repo."

**[SLIDE 8 — Deep dive: music_sec_dept] (7:20)**
"The hardest one, and the most honest story. It's a tiny virtual machine inside Pure
Data; an EXPORT command renders a 42-character string through a nonlinear keystream. We
traced the firmware, then — under time pressure — our second model, ChatGPT, used web
search and surfaced a published recipe. We disclose that plainly: a web search happened,
during the solve. What we can stand behind on the code is narrower and real: the
committed recovery worker inverts the key from the public `csaw{...}` structure and never
reads the expected answer at runtime, and an independent emulator reproduces a known
checkpoint byte-for-byte. We don't claim the conversation never saw the answer — it did.
We claim the derivation is answer-agnostic, and we let you judge the rest."

**[SLIDE 9 — The blocker] (8:30)**
"One we did not solve: an audio stego challenge. We genuinely decoded three of four
hidden fragments off the signal. The fourth is distorted spelled-out speech that beat
every demodulation and speech-recognition attempt we tried. We know the intended answer
— it's in the metadata — and we submitted nothing, because we couldn't derive it. An
unsolved challenge honestly reported is worth more to us than a value we can't stand
behind."

### P1 — Close (9:10–9:50)

**[SLIDE 10 — Lessons & close] (9:10)**
"Three takeaways. Parallel autonomous agents buy coverage, and git-per-branch means a
crash costs nothing. Environments, not cleverness, were our real blockers — a pinned
dependency and a missing runtime stopped us longer than any math did. And the thing we'd
repeat: audit your own run harder than a judge would, and publish what you find — even
when it's your first audit's mistake. 22 of 23 recovered, every one accounted for,
nothing hidden. Questions?"

## End-to-end explanation (own the technical narrative)

- **Coverage** came from six independent category agents on one VM, each on its own
  branch. Resilience came from committing continuously — proven when an overnight reboot
  cost us zero work.
- **Discipline** was one written rule (live-oracle or artifact derivation; metadata =
  cross-check). Writing it down is what let us audit against it.
- **Escalation**: the two hardest challenges used a deterministic multi-agent workflow
  with an adversarial verifier; music_sec_dept additionally used a second LLM.
- **Self-audit**: we parsed every transcript and prompt, found exposures our first pass
  missed (an answer in a prompt; under-counted reference use; a web search during a
  solve), and corrected the disclosure. The manifest (`MANIFEST.md`) and `DISCLOSURE.md`
  are the authoritative account; `ERRATA.md` lists known code/evidence limitations.
- **Outcome**: 22 recovered / 1 unsolved; 8 with no outside help, 12 reference-backed,
  2 answer-in-prompt, 1 web-searched. Eligibility is the organizers' to decide.

## Q&A defense pack — honest answers (assign a primary)

**"Did you use online write-ups?"** (P3) — "For one challenge, music_sec_dept, our second
LLM used web search and surfaced a public recipe. We disclose it, and the committed
derivation is answer-agnostic. For the rest, no web search was used in the solving
agents."

**"You used the challenge DB's author solutions."** (P2) — "Yes, for 12 challenges, and we
list them. We understand the organizers to permit the DB's own reference files; the
primary clarification isn't in our repo, so we label that as our understanding, not a
settled fact. Each reference solve was also run to produce the flag."

**"Two challenges had the flag in the prompt."** (P2) — "Correct — finders_keepers had the
plaintext answer and breach_zero_day had the author's full solve path. We found that in
our own audit and disclosed it. We don't claim those as answer-free; eligibility is yours
to decide."

**"Is music_sec_dept really your solve?"** (P3) — "The recovery worker's derivation is
answer-agnostic and reproduces an independent checkpoint — that's code-verifiable. But the
conversation that produced it had seen the metadata flag and a web-searched recipe, and we
say so. We're not claiming it never saw the answer."

**"Why is misc a blocker when the flag is in metadata?"** (P3) — "Because we derive it or we
don't claim it. The fourth fragment beat every decode we ran; submitting the metadata value
would be the one thing our whole approach exists to avoid."

**"How do we know your numbers?"** (P1) — "There's a per-challenge manifest with the flag,
basis, reference use, exposure, and a transcript pointer for all 23. The breakdown comes
straight from it; nothing is asserted that the evidence doesn't show."

**"What did your framework actually add?"** (P1) — "Orchestration and a multi-agent verify
workflow on top of Claude Code. We're precise about this in the errata: the workflow
*scripts* lived in the VM session dir and aren't committed, so we don't overclaim a
from-scratch framework."

## Delivery checklist
- Memorize the one honest headline sentence (top of this doc). Everyone can say it.
- Have `MANIFEST.md` and `DISCLOSURE.md` open in case a judge wants the per-challenge basis.
- Use real names; the `[P1]` placeholders and the 17:00 GST slot are administrative.
- No `.pptx` is committed yet — build slides from THIS script; if you present without a
  deck, this script stands alone.
- Time it twice; cut from slides 6 and 9 first if over 10:00.
- Do not revert to "every flag genuine / zero fabricated" language anywhere — it
  contradicts our own disclosure and a judge will catch it. The honest breakdown is the
  stronger talk.
