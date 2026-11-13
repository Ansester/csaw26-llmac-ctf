# Submission Repo Plan — personal GitHub now, official repo later

**Current state (verified):** everything is already on GitHub at
`github.com/Ansester/csaw26-llmac-ctf`, `master` @ `550c993`, tag `submission-v1`.
22/23 solved + 1 honest blocker; `SUBMISSION.md`, `solutions/FLAGS.md` (23 rows),
and `submission/transcripts/` (14 transcripts = the required proof) are all on
`master`. So the repo effectively exists — this plan is about making it clean,
safe, and ready to hand to the official repo when it lands.

## Decision: keep THIS repo as the submission home — do NOT squash or re-create
The full branch history + transcripts ARE the proof-of-work the contest wants
("submit the full conversation transcript"). A fresh squashed repo would throw
that away. Keep the history; just polish the top.

## Step 1 — Visibility: set the repo PRIVATE now
Until you actually submit, keep it private so other teams can't find your flags.
- GitHub → repo → Settings → Danger Zone → Change visibility → Private.
- Flip to public (or add the graders) only if/when the contest rules require it.

## Step 2 — Add a clean root README.md (navigation)
One page so a grader lands and immediately knows where everything is:
- One-line: "CSAW 2026 Quals — LLM-driven CTF, human-in-the-loop. 22/23 solved,
  1 honest blocker."
- Links: `SUBMISSION.md` (approach/methodology), `solutions/FLAGS.md` (all flags +
  the decoys-rejected section), `submission/transcripts/` (proof), `solutions/<cat>/`
  (per-challenge solvers + writeups), `prompts/` (the autonomous-agent briefs).
- A 6-row category table (crypto 4/4, forensics 4/4, web 6/6, pwn 3/3, misc 2/3,
  rev 3/3) — literals in FLAGS.md.
Commit to master; push. (The VM Claude or you can add this — it's the one missing
top-level file.)

## Step 3 — Pre-submission checklist (verify on master)
- [ ] `solutions/FLAGS.md` = 23 rows, 22 solved / 1 blocked, decoys section present
- [ ] `submission/transcripts/` populated + has a README mapping transcript→challenge
- [ ] `SUBMISSION.md` present and accurate (rev credited as second-LLM derivation,
      independently reproduced; native pd-l2ork = corroboration, not primary proof)
- [ ] every solved challenge has `solve_*.py` + `WRITEUP_*.md`; blocked has `BLOCKER_*.md`
- [ ] tag `submission-v1` points at the final commit
- [ ] no secrets/tokens committed (grep for `ghp_`, `.env`, keys) — scrub if found
- [ ] root `README.md` added

## Step 4 — When the official repo arrives (in a few hours)
Don't rebuild — mirror. From a clean clone of your repo:
```bash
git clone --mirror https://github.com/Ansester/csaw26-llmac-ctf.git
cd csaw26-llmac-ctf.git
git remote add official <OFFICIAL_REPO_URL>
git push official --all
git push official --tags
```
Or, if they want only `master`: `git push official master:main && git push official submission-v1`.
Keep your personal repo as the backup. If they instead give a submission *form*,
just paste the repo URL + commit hash `550c993` + tag `submission-v1`.

## Step 5 — Final submit
- Paste repo URL (or the official mirror) + commit `550c993` + tag `submission-v1`.
- Save the submission confirmation (screenshot/email) with the commit hash.

## Housekeeping (optional, non-blocking)
- Remove the leftover locked worktree once that other Claude session ends:
  `git worktree remove -f -f <path>`.
- The throwaway `challenge-repo/` re-clone and scratch dirs are already gitignored/
  uncommitted — leave them.
```
