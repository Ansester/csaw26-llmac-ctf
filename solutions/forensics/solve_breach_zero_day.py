#!/usr/bin/env python3
"""breach_zero_day solver. Usage: solve_breach_zero_day.py [artifact_dir]   (stdlib only)
Derives C2INDICATOR from pcap, SERVICENAME from the event log, BACKDOOR from the memdump, correlating timestamps:
  pcap  : monitoring host 10.14.0.9 goes silent at T_gap; the /api/sync C2 whose activity begins right after T_gap wins.
  xml   : the security service stopped (never restarted) just after T_gap, preceded by a kernel-driver install.
  mem   : strings stored reversed; meaningful ones are reassembled (high->low... see WRITEUP)."""
import base64, os, re, struct, sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone

d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "breach_zero_day_artifacts")
ts = lambda t: datetime.fromtimestamp(t, timezone.utc)

# ---------- pcap ----------
data = open(os.path.join(d, "fenwick_capture.pcap"), "rb").read()
e = "<" if struct.unpack("<I", data[:4])[0] in (0xA1B2C3D4, 0xA1B23C4D) else ">"
pk, off = [], 24
while off + 16 <= len(data):
    s, u, il, _ = struct.unpack(e + "IIII", data[off:off+16]); off += 16
    fr = data[off:off+il]; off += il
    if len(fr) >= 54 and fr[12:14] == b"\x08\x00" and fr[23] == 6:
        ihl = (fr[14] & 15) * 4; tcp = 14 + ihl; doff = (fr[tcp+12] >> 4) * 4
        pk.append((s + u / 1e6, ".".join(map(str, fr[26:30])), ".".join(map(str, fr[30:34])),
                   struct.unpack("!H", fr[tcp+2:tcp+4])[0], fr[tcp+13], struct.unpack("!I", fr[tcp+4:tcp+8])[0], fr[tcp+doff:]))
# monitoring gap
mon = sorted(p[0] for p in pk if p[1] == "10.14.0.9")
gaps = [(b - a, a, b) for a, b in zip(mon, mon[1:])]
big = max(gaps) if gaps else (0, 0, 0)
t_gap = mon[-1] if big[0] < 3600 else big[1]   # silent forever -> last check-in; else the biggest hole
print(f"monitoring host 10.14.0.9: {len(mon)} check-ins, last at {ts(mon[-1]):%H:%M:%S} UTC -> gap opens (never returns)")
# plaintext POST /api/sync, reassembled per flow ordered by seq
flows = defaultdict(list)
for p in pk:
    if p[6] and p[3] == 80 and p[1] == "10.14.22.47":
        flows[(p[1], p[2])].append(p)
cands = []
for (src, dst), ps in flows.items():
    ps.sort(key=lambda p: p[5]); body = b"".join(p[6] for p in ps)
    if body.startswith(b"POST /api/sync"):
        host = re.search(rb"Host: (\S+)", body).group(1).decode()
        b64 = re.search(rb'"id": "([^"]+)"', body).group(1)
        # per-destination connection activity
        syn = sorted(p[0] for p in pk if p[2] == dst and p[4] & 2 and not p[4] & 16)
        cands.append((host, base64.b64decode(b64).decode(), ts(ps[0][0]), len(syn), ts(syn[0]), ts(syn[-1])))
for c in cands: print("  candidate", c[0], "->", c[1], "| POST", f"{c[2]:%H:%M:%S}", f"| {c[3]} connections {c[4]:%H:%M:%S}..{c[5]:%H:%M:%S}")
# winner: first activity after the gap AND recurring beacon through the rest of the capture
win = [c for c in cands if c[4] >= ts(t_gap) and c[3] > 10]
assert len(win) == 1, cands
C2 = win[0][1]; print("C2 indicator (starts after monitoring gap, beacons thereafter):", C2)

# ---------- xml ----------
ns = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
ev = []
for x in ET.parse(os.path.join(d, "fenwick_security.xml")).getroot():
    s = x.find("e:System", ns); ed = x.find("e:EventData", ns)
    t = datetime.strptime(s.find("e:TimeCreated", ns).get("SystemTime"), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    ev.append((t, s.find("e:EventID", ns).text, {a.get("Name"): a.text or "" for a in ed} if ed is not None else {}))
ev.sort(key=lambda z: z[0])
stops = []
for i, (t, eid, dd) in enumerate(ev):
    if eid == "7036" and dd.get("param2") == "stopped" and dd.get("param1") in ("WinDefend", "SecurityHealthService", "Sense", "mpssvc"):
        nxt = next((u for u, e2, d2 in ev[i+1:] if e2 == "7036" and d2.get("param1") == dd["param1"]), None)
        restarted = next((u for u, e2, d2 in ev[i+1:] if e2 == "7036" and d2.get("param1") == dd["param1"] and d2.get("param2") == "running"), None)
        drv = [(u, d2["ServiceName"]) for u, e2, d2 in ev if e2 == "7045" and 0 < (t - u).total_seconds() <= 10]
        gap_delta = (t - ts(t_gap)).total_seconds()
        stops.append((t, dd["param1"], (restarted - t).total_seconds() if restarted else None, drv, gap_delta))
        print(f"  stop {t:%m-%d %H:%M:%S} {dd['param1']:22s} restart_after={(restarted-t).total_seconds() if restarted else None} driver_install_<=10s_before={drv} delta_vs_gap={gap_delta:.0f}s")
# the stop that is preceded by a driver install and lines up with the gap
w = [s for s in stops if s[3] and 0 <= s[4] <= 600]
assert len(w) == 1, w
SVC = w[0][1]; print("Service killed right after gap + driver load:", SVC)

# ---------- memdump ----------
toks = [(int(a, 16), b) for a, b in (l.rstrip("\n").split(" ", 1) for l in open(os.path.join(d, "fenwick_memdump.txt")))
        if re.fullmatch(r"[A-Z]{4,12}", b.split(" ", 1)[-1]) and " " not in b]
WORDS = {"FOREST", "TIGER", "MODULE", "FUD", "COPPER", "HEDGE"}  # reversed-token vocabulary spotted by eye among ~45 random upper-case strings
hits = [(a, b[::-1]) for a, b in toks if any(w in b[::-1] for w in WORDS)]
for a, r in hits: print(f"  mem {a:#x}: reversed -> {r}")
full = [r for a, r in hits if len(r) >= 9]            # complete names stored reversed = decoys (FUDMODULE, COPPERHEDGE)
frag = [(a, r) for a, r in hits if len(r) < 9]        # split fragments
# reading the dump back-to-front (strings are stored reversed, so the whole thing is reversed): later address first
BACKDOOR = "".join(r for a, r in sorted(frag, reverse=True))
print("complete reversed names (decoys):", full, "| split fragments assembled back-to-front:", BACKDOOR)
print("FLAG: csaw{%s_%s_%s}" % (C2, SVC.upper(), BACKDOOR))
