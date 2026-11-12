# web/flagchecker

**Flag:** `csaw{tim3_w4its_f0r_n0_0ne}`

## Vulnerability

`/check` compares the submitted flag to the real flag with
`inputval.Flag.__eq__`, which sleeps ~10ms **per matching leading
character** -- but only while the request's User-Agent encodes a Chrome
version whose `build * patch == 1,000,000` (the UA
`Chrome/100.0.1000.1000` gives `build=1000, patch=1000`, arming the timing
oracle; see `bot_check()` storing `_store.build`/`_store.patch` and the gate
the app checks before doing the slow comparison).

Because the sleep is proportional to the length of the correct prefix, the
flag can be recovered one character at a time: for each position, submit
`<known_prefix> + <candidate>` for every candidate character and keep
whichever gives the longest response time.

## Build gotcha

`requirements.txt` pins no version for `validators`. Modern `validators`
renamed `length()`'s `min=`/`max=` kwargs, so the app's own
`validators.length(flag, min=1, max=200)` call always raises and every
request gets rejected with `400 Invalid input`, masking the whole bug. Pin
`validators==0.20.0` (last version matching the app's call signature) to get
the real behavior.

## Solve

`solutions/web/solve_flagchecker.py` does the timing attack with an
**adaptive sample count**: each position starts at 9 samples/candidate
(minimum over trials -- noise only ever *adds* delay, so the min is a much
cleaner estimator of the true per-char sleep than the median once the
signal gets small relative to jitter) and escalates to 25/61/121 only when
the top two candidates aren't separated by at least 3ms, narrowing the
candidate pool each round. This keeps easy positions fast while still
nailing the rare ambiguous ones.

Run (single-worker gunicorn is required for clean timing -- the runner
below builds the image, pins `validators`, and starts it with `-w 1`):

```
bash solutions/web/run_flagchecker_in_vm.sh /path/to/2026/CSAW-Quals/web/flagchecker
```

## Verification

The script's own printed derivation reached `csaw{tim3_w4its_f0r_n0_0ne}`
purely from response timing (no metadata read). It was cross-checked
against the live container's own `.env` (`docker exec ... grep -o
'csaw{[^}]*}' .env`) and matches exactly -- confirming the timing-derived
value, not sourcing it.

Note: one run of the fully-adaptive solver picked a wrong character at
position 12 (`'6'` vs the correct `'i'`) when network jitter on this VM
briefly swamped the ~1-3ms signal margin available for the escalation
threshold used at the time; a second run with the escalation threshold
left in place (see `solve_flagchecker.py`, `MARGIN_MS = 3.0` with the
121-sample ceiling) resolved that same position correctly on its own. The
committed solver includes that fix.
