# Self-Audit & Disclosure — CSAW 2026 Quals LLM-CTF (corrected 2026-11-13)

This is a corrected version. An earlier pass of this file understated two things,
which a deeper review of the prompts and solver code caught:
1. It searched only for `csaw{...}`-shaped strings, so it **missed a plaintext answer
   that was present in a solving prompt** (`finders_keepers`).
2. It undercounted reference-solution use (several solvers self-describe as
   reference-based in their own source).
Both are corrected below. Nothing in the committed transcripts/prompts was edited to
hide this — the exposures are visible in the committed files and are cited here.

## Status definitions (kept separate on purpose)
- **Recovered**: a flag string was produced by a live service or a script we ran.
- **Exposure/reference history**: whether the solving context already contained the
  answer, an author reference solution, or online material.
- **Eligibility**: whether a recovery earns competition credit. **That is the
  organizers' decision, not ours.** We do not assert eligibility anywhere in this file.

## Organizer clarifications — reported, not substantiated here
We asked the organizers (Discord modmail) about (a) using the challenge DB's own
reference files and (b) reproduction requirements, and understood the replies to be:
DB reference files are permitted, "no write-ups" targets web search, and reproduction
is not required. **The organizers' actual reply is not committed in this repository**,
so treat the above as the team's reported understanding pending that primary evidence.
Separately, the brief's rule that prompts must not contain direct solutions is not
waived by a reference-file allowance; the two answer-in-prompt cases below are flagged
for the organizers regardless.

## Recovery / exposure summary (22 recovered, 1 unsolved)
- **~8 recovered with no reference acknowledgement and no answer in the prompt**:
  polly, taking_on_the_temple, hemispheres, schrodingers_backup, keep_walking_forward,
  autobahn, flagchecker, juggler (juggler's writeup states it was solved from scratch).
- **~11 used an author reference solution / generator** (acknowledged in the solver
  source — permitted material under our reported understanding, but disclosed):
  secret_treaties, ghost_in_the_machine, hells_bells, saint_vespers, machine_head,
  low_tide, diamond_dogs, trustdinoidc, csale, golf_heist, house_of_hollow_houses.
  Each was additionally run to produce its flag.
- **2 had the answer or full solve path in the solving prompt** (disclosed; eligibility
  is the organizers' call):
  - `finders_keepers` — the plaintext answer `cantfindit` is in `prompts/category/
    crypto.md` and in the initial user message of the crypto session. The video
    extraction was also performed, but the context was not answer-free.
  - `breach_zero_day` — the challenge author's "Intended Solve Path" (steps 1–7) and
    the exact flag were supplied in a user message.
    (`secret_treaties` also received an English rendering of its flag + the intended
    technique in the prompt, on top of its reference solver.)
- **1 had online-material exposure during the solve** — `music_sec_dept` (see below).
- **1 unsolved** — `misc/12345678` (3 of 4 audio fragments recovered; no flag submitted).

## music_sec_dept — accurate chronology (corrects the earlier "post-hoc" framing)
In order, from the committed external ChatGPT transcript:
1. The metadata flag `csaw{~i_love_my_computer_&_it_loves_me~<3}` was present in the
   approach-seeking prompt from the start (`prompts/CONSULT_SECOND_OPINION.md`).
2. Artifact analysis traced the firmware transform.
3. On a request for an immediate solution, the second LLM **searched the web/GitHub and
   surfaced a published recipe** (`KEY bf03942fbd12`, `EXPORT 9a3f000000`).
4. **Only afterward** was the completed independent recovery + interpreter verification
   claimed.
The earlier statement that the online material was "seen only as a post-hoc cross-check
after the derivation" is **not accurate** and is withdrawn. What can be supported by
code inspection is narrower: the committed recovery worker's derivation does not read
the expected flag at runtime (it inverts from the public `csaw{`/`}` structure plus a
fixed 10-char EXPORT argument and a readability ranking). That is a statement about the
implementation, not about a conversation that had never seen the answer — the
conversation had. Eligibility is for the organizers.

## Other corrections to earlier claims
- Reference use: `trustdinoidc` ("based on the challenge's own solver_files/solve.py"),
  `csale` ("reference solver (unmodified)"), `golf_heist` ("automates [the author
  walkthrough]"), `house_of_hollow_houses` ("used the generator's plaintext comment to
  learn the signature→letter table"), `secret_treaties` ("reference solver") were
  previously marked "no reference." Corrected above.
- "Unaltered transcripts": the orchestration transcript is a **privacy-sanitized export**
  (the submitter email is replaced with `[submitter-email-redacted]`). No credential was
  found in the committed text; the sanitization is the one deliberate transformation.
- Decoys rejected (unchanged, and genuinely rejected): csale `csawctf{th1s_wAs_EZ}`;
  two misc "AI-detection" honeypot flags; the music_sec_dept 13-char KEY string (note:
  the real KEY handler is a lenient byte parser, not a password compare — the "13-char
  decoy vs 12-char real" framing was an early hypothesis, not a settled fact).

## Bottom line
**22 of 23 challenges have a recovered flag; 1 is unsolved.** Of the 22, roughly 8 had
no reference or answer exposure, ~11 used permitted author references (disclosed), 2 had
the answer in the prompt, and 1 had online-material exposure during the solve. We make
no claim about how many earn credit — that is the organizers' adjudication. Full
trajectories, prompts, and solver code are included so they can decide on the evidence.
