# CSAW 2026 Quals — LLMAC_DB solutions

Working repo for https://github.com/NYU-LLM-CTF/CSAW26_LLMAC_DB (2026/CSAW-Quals).

Staging ground only — will be re-uploaded to the official submission repo later.

## Layout
- `solutions/<category>/solve_<name>.py` — reproducible solver (run it, it prints the flag)
- `solutions/<category>/WRITEUP_<name>.md` — vuln + technique + how to run
- `solutions/<category>/BLOCKER_<name>.md` — only for genuinely blocked challenges, with the exact reason
- `solutions/FLAGS.md` — master table, built once the category is done
- `prompts/` — the operating prompts used to drive the solve (kept for reproducibility)

## Ground rules (see prompts/MEGA_PROMPT.md for the full version)
- Genuine solves only. Every flag must come from running a script against a live
  target or decrypting/deriving it — never hardcoded, never pattern-matched.
- This repo's upstream (CSAW26_LLMAC_DB) ships a reference `solve.py`/`writeup.md`
  for 15 of the 22 challenges. Treat those as a hypothesis: run them against a
  freshly-built instance and independently confirm the flag, don't just copy them.
- Several challenges ship decoy flags in correct `csaw{...}` format specifically to
  catch agents pattern-matching instead of verifying (e.g. misc/keep_walking_forward's
  "AI Detection Flags"). A flag counts only when the target/artifact itself confirms it.
