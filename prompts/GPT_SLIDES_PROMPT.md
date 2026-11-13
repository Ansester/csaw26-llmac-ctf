You are building a conference-style slide deck for a 10-minute CTF presentation.
Produce a downloadable PowerPoint (.pptx) — generate it with python-pptx in your
code tool and give me the file. ~10 slides, clean technical style (dark or light,
high contrast, minimal text per slide, monospace for code/flags, one idea per
slide). Put the talking points in the speaker-notes of each slide, not on the
slide face. Use everything below as the content; don't invent results.

CONTEXT (all true, use verbatim where it's a flag/number):
- Event: CSAW 2026 Quals, NYU LLM-CTF database. Approach: LLM-driven, human-in-the-
  loop (HITL). No manual solutions or human write-ups; humans gave hints, set up the
  environment, and reviewed every flag.
- Final result: 22 of 23 challenges solved and verified; 1 honest blocker.
- Hard rule enforced throughout ("the IRON RULE"): a flag counts ONLY if a live
  service accepts it OR it is derived end-to-end from the challenge's own artifacts
  by a script that was run and watched produce it. Metadata/`info.md` flags are
  cross-check only. Several challenges ship DECOY flags; they were caught and refused.

SLIDES (titles → key points; expand the notes yourself):
1. Title — "LLM-Driven CTF, Human-in-the-Loop" · CSAW 2026 Quals · [team names] ·
   22/23 solved, 1 honest blocker.
2. Thesis — autonomous LLM agents + strict genuineness beats one model grinding
   serially. Self-imposed constraints: disposable VM, no spend, nothing on the host.
3. Architecture — 6 parallel autonomous Claude Code sessions (one per category:
   crypto, forensics, misc, pwn, rev, web) in tmux on an isolated VirtualBox VM;
   git branch-per-category, push-as-you-solve; an orchestration/HITL layer that
   authored structured agent briefs and reviewed every flag. (Note in speaker notes:
   an overnight VM reboot killed all 6 sessions and ZERO work was lost — everything
   was already committed.)
4. The IRON RULE — the genuineness standard (state it as in CONTEXT). This is what
   makes the submission trustworthy and what cost us one challenge we wouldn't fake.
5. Anti-fabrication in action (the key slide) — decoys caught and NOT submitted:
   csale honeypot `csawctf{th1s_wAs_EZ}` (wrong prefix); music_sec_dept 13-char KEY
   decoy vs the real 12-char key; music_sec_dept's `info.md` string + `EXPORT 9a3f`
   decoy render treated as cross-check only. Enforced structurally with adversarial
   verifier agents that re-run candidates and reject anything not genuinely derived.
6. Results — 22/23. Category table: crypto 4/4, forensics 4/4, web 6/6, pwn 3/3,
   misc 2/3, rev 3/3. Every solved flag backed by an oracle hit or a script-run
   derivation.
7. Deep dive — web/flagchecker. A custom `__eq__` sleeps ~10 ms per matching leading
   char (a timing oracle), armed only by a crafted Chrome UA (build×patch = 1,000,000).
   Recovered the flag char-by-char using the MIN response time (jitter only adds
   delay), confirmed by the service's own `{"correct": true}`.
   Flag: `csaw{tim3_w4its_f0r_n0_0ne}`.
8. Deep dive — rev/music_sec_dept (the hardest, and an honesty showcase). A Pure Data
   "VM": `EXPORT` renders a 42-char string via a nonlinear keystream folded mod-95.
   Recovered the 12-hex KEY by an ANSWER-AGNOSTIC inversion constrained only on the
   public `csaw{`/`}` syntax (12,288 states → 87 valid → real flag ranks #1 by a
   generic alphabet score, 67 vs 61), replayed through an independent emulator
   validated byte-for-byte against the known decoy render. Honesty note: the initial
   derivation came from a SECOND LLM and was then INDEPENDENTLY REPRODUCED and cross-
   checked in our environment before we committed it — disclosed, not hidden.
   Flag: `csaw{~i_love_my_computer_&_it_loves_me~<3}`.
9. The honest blocker — misc/12345678 (audio stego). 3 of 4 leetspeak fragments
   genuinely decoded from the signal (reversed-channel ASR, metadata base64, a
   rendered tone-bitmap OCR'd against a public font). The 4th is ring-modulated /
   frequency-shifted spelled speech that defeated the full answer-agnostic battery;
   we returned null rather than hardcode the known value. A blocker, by choice.
10. Lessons & close — parallel autonomous agents → broad coverage; git-per-branch →
   nothing lost; genuineness as a first-class rule → every decoy caught, zero
   fabricated flags; an honest blocker beats a wrong flag. Proof: full session
   transcripts + per-challenge repro are included in the submission.

Timing: ~1 min/slide ≈ 9:45. Expand slides 5 and 3 if you have slack; trim 2 and 10
if over. After generating the .pptx, give me a one-paragraph summary of the deck and
the download link.
