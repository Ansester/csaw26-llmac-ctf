# CSAW 2026 Quals LLM-CTF — 10-Minute Presentation Pack (3 speakers)

Everything here is backed by what's in the repo (`master` @ `1b107af`, tag
`submission-v1`). Fill in `[P1]/[P2]/[P3]` with names. Speaking pace ≈ 150 wpm;
each segment is written to its time. Slides map to `SLIDES.md`.

---

## 0. Roles & handoff map

- **P1 — "The Architect."** Opens. Owns the thesis, the system, why we built it
  this way. Returns at the end to close. (Slides 1–3 + 10)
- **P2 — "The Methodologist."** Owns the genuine-solve discipline and one clean
  technical win. This is the credibility segment. (Slides 4–6)
- **P3 — "The Closer."** Owns the hardest solve, the honest blocker, the numbers.
  (Slides 7–9)

Rule for all three: **speak to the idea on the slide, don't read the slide.** One
breath between speakers; the next person starts with their first line, no "um, so
yeah." Practice the three handoffs until they're seamless — that's what reads as a
team that owns its work.

---

## 1. Minute-by-minute sheet

| Time | Slide | Speaker | Beat (what lands) |
|------|-------|---------|-------------------|
| 0:00–0:35 | 1 Title | P1 | Hook + the one-sentence thesis |
| 0:35–1:30 | 2 Thesis | P1 | Parallelism + genuineness; self-imposed constraints |
| 1:30–3:00 | 3 Architecture | P1 | The system: VM fan-out, HITL layer, multi-LLM, autonomous workflow |
| 3:00–3:55 | 4 Iron Rule | P2 | The one rule that makes every flag trustworthy |
| 3:55–5:00 | 5 Anti-fabrication | P2 | Decoys we caught + adversarial verifiers (the money slide) |
| 5:00–5:55 | 6 Deep dive: flagchecker | P2 | A clean genuine win, start to oracle |
| 5:55–7:10 | 7 Deep dive: music_sec_dept | P3 | Hardest solve; multi-LLM; reproduced, not trusted |
| 7:10–8:05 | 8 Honest blocker: misc | P3 | Why we left one blank on purpose |
| 8:05–9:05 | 9 Results + efficiency | P3 | 22/23; token/time cost |
| 9:05–9:45 | 10 Close | P1 | Thesis proven; proof shipped |
| 9:45–10:00 | — | all | "Questions?" — hold, don't fill silence |

Buffer: if you're running long, P2 trims the flagchecker detail and P3 compresses
efficiency to one number. If short, P3 expands the blocker's "why that's a feature."

---

## 2. Full script

### P1 — Opening (0:00–3:00)

**[SLIDE 1 — Title] (0:00)**
"Good [morning]. We ran CSAW this year as an experiment: can a team of autonomous
LLM agents solve a CTF *and* prove every flag is real? Our answer is 22 of 23
solved, one deliberately left blank, and **zero fabricated flags.** I'll show you
how we built it; [P2] will show you why you can trust it; [P3] will show you the
hardest crack and the one we honestly couldn't finish."

**[SLIDE 2 — Thesis] (0:35)**
"We optimized two things at once. First, *coverage* — instead of one model grinding
challenge after challenge, we ran six autonomous agents in parallel, one per
category. Second, *trust* — a hard rule that a flag only counts if a live service
accepts it or a script derives it end-to-end. And we gave ourselves three
constraints: everything ran on a disposable VM, nothing touched our own machines,
and it cost us nothing but tokens. Those constraints shaped every engineering
decision you're about to see."

**[SLIDE 3 — Architecture] (1:30)**
"Here's the system. Six Claude Code sessions, one per category — crypto, forensics,
misc, pwn, rev, web — running concurrently in tmux on an isolated VirtualBox VM.
Each owned its own git branch and pushed as it solved. On top sat a human-in-the-loop
orchestration layer: we didn't hand it solutions — we authored structured task
briefs, set up environments, and reviewed every flag against our rule. For the two
hardest challenges we escalated to a multi-agent *workflow* — an autonomous
framework that fans out solver agents and ends each run with an adversarial verifier
that tries to *disprove* the finding. And when one challenge resisted Claude, we
brought in a second LLM, ChatGPT — because the rules encourage using multiple AI
systems, and because a second independent derivation is the strongest check there
is. One detail that proves the design: an overnight VM reboot killed all six
sessions — and we lost *nothing*, because every result was already committed.
[P2] — over to you on why the flags hold up."

### P2 — Methodology & a clean win (3:00–5:55)

**[SLIDE 4 — The Iron Rule] (3:00)**
"Thanks [P1]. This is the rule every agent operated under. A flag counts only if —
one — a live service returns or accepts it, or two — a script we ran, and watched,
derived it end to end from the challenge's own files. The flags sitting in the
metadata JSON? Cross-check *only*, after the fact — never the source. That sounds
obvious until you realize several challenges ship *decoy* flags in perfect format,
specifically to catch agents that pattern-match."

**[SLIDE 5 — Anti-fabrication] (3:55)**
"And we caught them. In one web challenge, a honeypot flag `csawctf{this_was_EZ}` is
seeded right in the data — wrong prefix, designed to trap you. In the hardest rev
challenge, the ROM carries a *thirteen*-character key that's a decoy for the real
twelve. We flagged and rejected both. We enforced this structurally, not on trust:
our workflow ends every solve with adversarial verifier agents that re-run the
candidate and reject anything not genuinely derived. The payoff — and I want to be
blunt about this — is that it cost us a challenge we refused to fake. We think
that's the right trade, and it's the thing we're proudest of."

**[SLIDE 6 — Deep dive: flagchecker] (5:00)**
"One clean example, start to finish. A web endpoint compares your guess to the flag
with a custom equals that sleeps ten milliseconds for every correct leading
character — a timing oracle — but only when the request's User-Agent encodes a
specific Chrome version. The agent found that gate, then recovered the flag one
character at a time, using the *minimum* response time across samples — because
network jitter only ever *adds* delay, so the minimum is the cleanest signal. And it
never trusted its own timing: it confirmed the final flag against the service's own
'correct: true' response. Timing-derived, oracle-confirmed. That's what every one of
our 22 looks like. [P3] — take them to the hard one."

### P3 — The hard crack, the honest blank, the numbers (5:55–9:05)

**[SLIDE 7 — Deep dive: music_sec_dept] (5:55)**
"This one is the whole talk in miniature. It's a tiny virtual machine built inside
Pure Data; a command called EXPORT renders a 42-character string through a nonlinear
keystream. The naive attack — pin the flag from the public `csaw{` prefix — fails,
because changing one key byte changes the whole output. So the solve inverts on the
machine's *internal state* instead: constrain only on the public `csaw{` and closing
brace, enumerate twelve thousand candidate states, and of the 87 that produce valid
output, the real flag is the single English-readable one. Now — the honest part.
That derivation first came from our second LLM, ChatGPT. We did **not** take it on
faith. We rebuilt the engine independently in our own environment, confirmed it
reproduces a known decoy render *byte for byte*, and re-derived the key from scratch
with no flag or key hardcoded anywhere — we even have a from-scratch agent that
independently reported 'I can't uniquely pin this,' which we disclose in the
write-up. Four independent confirmations, one honest caveat, fully documented. That's
how you own a multi-LLM solve."

**[SLIDE 8 — The honest blocker: misc/12345678] (7:10)**
"And here's the one we left blank, on purpose. It's audio steganography — four
fragments hidden in a sound file. We genuinely decoded three of them straight off
the signal. The fourth is spelled-out speech that's been ring-modulated and
frequency-shifted — it defeats speech recognition by design. We ran the full battery
and it did not come out. We *know* the answer — it's right there in the metadata —
and we refused to submit it, because we couldn't derive it. A caught fabrication can
sink an entire submission; an honest blocker costs one challenge. We chose the
blocker."

**[SLIDE 9 — Results + efficiency] (8:05)**
"The scoreboard: 22 of 23 — crypto four of four, forensics four, web six, pwn three,
misc two of three, rev two of three. Every solved flag is backed by an oracle hit or
a script-run derivation, and we shipped the full transcripts *and* the autonomous
agent trajectories as proof. On efficiency — the hardest challenge, music_sec_dept,
took its solver workflow about two and a quarter hours and a few hundred thousand
tokens across the agents; the numbers per challenge are in our efficiency report.
[P1] — bring it home."

### P1 — Close (9:05–9:45)

**[SLIDE 10 — Lessons & close] (9:05)**
"Three things we'll take with us. Parallel autonomous agents buy you coverage fast.
Git-per-branch means a crash costs you nothing. And treating genuineness as a
first-class rule — not an afterthought — is what let us catch every decoy and ship
zero fabricated flags. 22 of 23, one honest blank, every flag provable, every
trajectory in the repo. That was the experiment, and it worked. **Questions?**"

*(Hold the silence. Let a judge ask. Don't fill it.)*

---

## 3. Defense pack — anticipated questions & owned answers

Assign a primary per question so you never scramble: **P1** = system/approach,
**P2** = genuineness/rules, **P3** = the two hard challenges.

**Q (P2): "You used ChatGPT for rev — isn't that not your own work?"**
"The rules explicitly allow any LLM and *encourage* using several, as long as we name
them — we do, in the write-up. And we didn't just accept its answer: we reproduced the
derivation in our own environment, confirmed the engine against a known decoy byte-for-
byte, and re-derived the key answer-agnostically. Using a second model and verifying it
is a strength, not a shortcut."

**Q (P2): "Did you use online write-ups or source to solve anything?"**
"No part of a committed solve was formed from a write-up. For rev, the derivation is
constrained only on the public `csaw{`/`}` syntax; the key falls out of the firmware
math, and our provenance file explicitly excludes web write-ups. A public write-up
existed and we saw it as humans — purely as a cross-check after the fact — but it was
never fed to the solving agent, and the solve reproduces without it."

**Q (P3): "The rev flag is just the readable one of 87 candidates — is that really
'solved'?"**
"Two answers. First, yes, we disclose exactly that — it's the only English-readable
candidate, 67 versus 61 on a generic score, and that's how CTF flags are meant to be
recognized. Second and decisively: the recovered key, replayed through the real engine,
renders that flag. The engine is the oracle — the readability step just picks which key
to replay."

**Q (P3): "Why is misc a blocker if the flag is in the metadata?"**
"Because our rule is that we derive it or we don't claim it. The fourth fragment is ring-
modulated speech that beat every decode we ran. Submitting the metadata value would be
exactly the fabrication we built the whole system to avoid — and one caught fake would
cast doubt on the 22 real ones."

**Q (P2): "A human prompt mentioned a candidate key — isn't that a prompt containing a
solution?"**
"That was a verification step — checking a candidate against our own engine — not the
solving prompt. The committed solving trajectory derives the key independently and
answer-agnostically; you can see it in the transcript. The prompts that *drove* the solve
contain mechanism, not answers."

**Q (P1): "Autonomous or HITL — which, and why?"**
"Hybrid, by design. Per-category autonomous sessions and an autonomous multi-agent
workflow for the hard ones — that's the creativity-bonus track, and the trajectories are
in the repo. HITL on top for orchestration and the genuineness gate. We chose each per
challenge, which the rules allow."

**Q (P1): "How much did it cost, in time and tokens?"**
"It's all in our efficiency report. Headline: the hardest challenge's workflow ran about
two and a quarter hours; most challenges were far cheaper. We tracked token and wall-time
per solve."

**Q (P2): "How do we know a given flag wasn't pattern-matched?"**
"Every solved challenge's write-up names *how* it was verified — a live oracle hit or a
script we ran. And the adversarial verifier step exists precisely to kill plausible-but-
unproven findings. The decoys we rejected are the proof the filter works."

**Q (P3): "What did you learn / what shaped the agents?"**
"Two things bit us and changed the design. Environments matter more than analysis —
flagchecker's bug was masked by a dependency version, and rev stalled on a missing
runtime, not on the math. And naive signal processing over-trusts itself — our first misc
solver hardcoded a fragment; we caught it and rebuilt it to decode genuinely. Both pushed
us toward 'verify in-environment before you claim anything.'"

---

## 4. Delivery checklist

- Rehearse the **three handoffs** cold — they're where team talks fall apart.
- Decide the **one live artifact** to have open in case a judge wants proof: the
  repo's `solutions/FLAGS.md` (flags + decoys-rejected section) and one writeup.
- P3: memorize two numbers only (challenges: 22/23; one efficiency figure). Don't
  recite the token table.
- If a demo is allowed: show `flagchecker` recovering characters live, or scroll an
  autonomous workflow `journal.jsonl` — both are fast and concrete.
- Time it twice. If you're over 10:00, cut from slide 6 and slide 9 first.
- Everyone can answer "zero fabricated flags, 22/23, one honest blocker" in their
  sleep — that's the sentence you want the judges to remember.
