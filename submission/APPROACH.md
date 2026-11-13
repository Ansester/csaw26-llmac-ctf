# Approach — prompting, tools, and model/harness choices

This makes explicit the prompting techniques, tool usage, and model/harness decisions
behind the run. The actual prompts are in `framework/prompts/`; the solvers are in
`framework/solutions/`; the honest per-challenge account is in `DISCLOSURE.md` /
`MANIFEST.md`.

## Harness & model choice (and why)
- **Harness: Claude Code agents** (CLI, tool-using) running on a disposable VM, one per
  category, in parallel tmux panes. Chosen for strong tool use (shell, file edit, running
  solvers live), long-horizon autonomy, and a built-in **multi-agent Workflow** facility we
  used for the hardest challenges. Isolation on a throwaway VM gave us $0 cost, no risk to
  our own machines, and — with git-branch-per-category — crash resilience (proven twice: an
  OOM crash and an overnight reboot, both recovered with ~no lost work).
- **Models (recorded in the logs):** `claude-opus-5-5` and `claude-opus-4-8` for the
  hardest reasoning / reverse engineering; `claude-sonnet-5-5` and `claude-sonnet-5` for
  breadth and cheaper categories. Rationale: Opus-tier for the deep RE (music_sec_dept) and
  pwn heap work; Sonnet-tier where the task was more mechanical, to keep token cost down
  (see `EFFICIENCY.md` — crypto/forensics/pwn were each < ~35k output tokens total).
- **Second LLM: ChatGPT**, used on the single hardest challenge (`music_sec_dept`) as an
  independent second opinion. The rules encourage multiple AI systems; we name it and
  disclose exactly what it did (including a web search — see `DISCLOSURE.md`).

## Prompting techniques
1. **Structured category briefs** (`framework/prompts/category/*.md`). Each agent got a
   self-contained brief: the environment, the deliverable format, a per-challenge status
   list, and — centrally — the **genuine-solve ("iron") rule**. These are reusable,
   category-scoped system prompts rather than per-challenge hand-holding.
2. **A standing "iron rule" pattern**, repeated in every brief: a flag counts only if a
   live service accepts it or a script we run derives it; the metadata flag is cross-check
   only; and named **decoy warnings** (the challenges plant honeypot flags, so we told the
   agents to expect and reject them — which they did, e.g. the csale and misc honeypots).
3. **Reference-use instruction** (disclosed): the briefs told agents they may read the
   challenge DB's **author reference solutions** and model their solver on them, then re-run
   live to produce the flag. ~12 solves used this (see `MANIFEST.md`).
4. **Separation of solving vs. reproduction prompts.** Prompts that *drove a solve* carried
   mechanism, not answers; later **reproduction/verification handoff prompts** (clearly
   post-solve) re-ran an already-derived result to confirm it. We keep these distinct so the
   record is auditable.
5. **Multi-agent workflow with adversarial verification** (the creativity-bonus technique).
   For the two hardest challenges we ran a deterministic workflow that **fans out several
   solver agents** on different attack angles and ends each run with an **adversarial
   verifier agent** whose only job is to *disprove* the candidate (structured/`schema`
   outputs so a verdict is machine-checkable). This is what caught a back-fit misc decode and
   forced an honest blocker.
6. **Second-opinion consultation prompt** (`framework/prompts/CONSULT_SECOND_OPINION.md`):
   a self-contained brief handed to the second LLM, framed to keep any derivation
   **answer-agnostic** (derive from the public `csaw{...}` structure, never from the known
   string).
7. **Human-in-the-loop steering.** The orchestration session authored and refined the
   prompts, reviewed every flag against the iron rule, reconciled state after crashes, and —
   importantly — ran the **self-audit** that corrected our own first disclosure.

## Tool usage (by where it mattered)
- **Orchestration:** Claude Code + its multi-agent Workflow; tmux (parallelism); git
  branch-per-category + continuous commits (resilience); the VM (isolation).
- **rev:** Ghidra / `capstone` / `pyelftools` for static RE; a from-scratch Python emulator
  of the challenge's VM; Purr-Data / pd-l2ork for the Pure Data VM challenge; qemu where a
  Linux binary had to run.
- **pwn:** `pwntools`, bundled libc, heap-exploitation primitives (UAF / tcache) against
  freshly-built containers.
- **web:** `requests`/urllib, `PyJWT` (token forging), SQL-injection + IDOR tooling, a
  timing-attack harness; Docker for local service builds.
- **crypto:** `pycryptodome`, lattice reduction (LLL), GF(2) linear algebra, a server oracle.
- **forensics:** `scapy` (pcap), `pefile`/`dnfile` (.NET/PE), `py7zr`, SQLite WAL replay,
  stego tooling.
- **misc (audio):** `numpy`/`scipy`/`Pillow` (spectrogram + bitmap decode), `faster-whisper`
  (ASR), demodulation experiments.

## Challenges that shaped our approach & what we learned
Concrete moments where a problem changed how we built the agents (the rules ask how
specific challenges affected our agent engineering):
- **An out-of-memory crash killed all six agents early on** → we made *commit-and-push
  after every step* and *one git branch per category* non-negotiable. It paid off again
  when the VM rebooted overnight — zero work lost both times.
- **`music_sec_dept` needed a runtime we couldn't stand up** (Purr-Data; Docker was
  unavailable) → we learned that *environments, not analysis, were our real blockers*, and
  pivoted from "run the real thing" to a from-scratch offline emulator validated against a
  known checkpoint.
- **`flagchecker`'s vulnerability was hidden by a dependency version** (a `validators` API
  change made every request fail with 400) → the agent had to fix the environment before
  the bug was even visible; dependency pinning matters as much as the exploit.
- **Our first misc audio solver hard-coded a fragment** (a back-fit) → we added the
  **adversarial-verifier** step to the workflow specifically to catch answers that aren't
  genuinely derived; it forced us to honestly leave the 4th fragment unsolved.
- **Our own first self-audit was too generous** (it missed a plaintext answer sitting in a
  prompt) → we built a machine-readable manifest and a deeper second audit, and corrected
  the disclosure in writing.
- **The multi-LLM episode** (a second model web-searched a recipe) → we tightened the rule
  that a committed derivation must be *answer-agnostic*, and we disclose the exposure rather
  than hide it.

## What we do NOT claim about the framework
The "framework" is Claude Code and its built-in Workflow facility, orchestrated with our
prompts — **not** a from-scratch agent framework. The workflow *scripts* themselves ran in
the VM session directory and are not committed (see `ERRATA.md`). We describe what we
actually used rather than overclaim original tooling.
