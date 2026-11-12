# web/low_tide

**Flag:** `CSAW{time_sensitive_scada_proxy_chain}`

Note the uppercase `CSAW{...}` — this challenge's own `challenge.json` /
`docker-compose.yml` (`FLAG=CSAW{time_sensitive_scada_proxy_chain}`) ship it
uppercase, unlike every other 2026 challenge's lowercase `csaw{...}`. Do not
normalize the case when recording/submitting it.

## Architecture

Five services, chained:

- `phase0-static` — nginx, static recon page only (not needed for the flag).
- `load-balancer` (`lb_app.py`) — public entrypoint. Requires an exact
  `User-Agent: StationSync-Agent/2.1`, assigns each new session to one of 4
  backend stations at random, enforces a burst limit (5 req / 5s) and a
  "lap" limit (4 wrong-token attempts rotates you to another station; a
  full 4-station cycle triggers a 16s cooldown).
- `station-{1..4}` (`station_app.py`) — each on its own deliberately-wrong
  clock (`TARGET_TIME` env var). Auth: `token = md5(identity + station_epoch)`
  where `identity` is the session's `sid` cookie (first login) or the
  `station_id` (every request after). The station leaks its own
  `sync_time` on every *rejected* attempt.
- `admin-relay` (`admin_app.py`) — never reachable directly; only
  station-4 can proxy to it (`IS_RELAY_STATION=true`). Holds a simulated
  water-tank level starting at 70; landing exactly on 20 returns the flag.

## Chain (automated in `solve_low_tide.py`)

1. **Login / token forging.** POST `action=checkin&token=x` (any session
   with the required UA gets a `sid` cookie) — the rejection response
   leaks `sync_time` for that session's randomly-assigned station. Anchor
   to that epoch with `time.monotonic()` (not a fresh probe per request —
   see "Pacing" below), compute `md5(sid + epoch)`, and check in again.
   Success returns `station_id`.
2. **Virtual filesystem walk** (`/station/checkin/api/v1/<station_id>/...`,
   same anchored-epoch token scheme, now keyed by `station_id` instead of
   `sid`): root listing → `station.log` names a hidden
   `.logs/err_3005.log` (never listed) → that file says the chat bridge
   "relocated" to `config/relay_chat.js` → `config/relay-bot.js` (base64)
   is a dead end/flavor text → `config/sync.conf` gives the **second**
   token formula used by the chat API:
   `md5(station_id + mon + dd + yy + HH + MM)` (minute-granularity, no
   seconds — Authorization header, not form token).
3. **Chat log** (`GET /station/checkin/api/v2/chat?id=N`, `Authorization:
   Bot <chat_token>`, pages of 5): paging through all 60 messages, #53–55
   reveal the admin-relay host (`10.10.14.31`) and the relay key
   (`4f9a-77c2-e01d`), and that only station 4 has the relay route wired up.
4. **Get onto station 4.** Station assignment is random per session; keep
   starting fresh sessions (full login, step 1) until one lands on
   `station_id == "st-04"`.
5. **Relay.** `POST /station/checkin/relay` with
   `X-Relay-Target: 10.10.14.31`, `X-Relay-Key: 4f9a-77c2-e01d`,
   `cmd=CMD:WATER:LOWER:50` (tank starts at 70, so one call lands exactly
   on the target of 20) — the admin-relay's response embeds the flag when
   the level hits exactly 20.

## The pacing trap (why a naive port of the reference solve breaks)

The challenge's own `solve.py`/`full_solve.py` call a fresh "probe"
(`token=x`, always rejected) before *every single* subsequent request just
to re-read the station's clock. Each such probe is itself a wrong-token
attempt and counts against the load balancer's 4-strikes-per-station lap
counter (`handle_lap_accounting` in `lb_app.py`) — four of these in a row
silently **rotates you off the station you just carefully logged into**,
which breaks the virtual-filesystem walk (now computing tokens for a
station you're no longer on) with no error beyond a generic "rejected".

Our solver instead anchors to the station's epoch **once** per station
(one probe) via `time.monotonic()`-based prediction, and derives every
following token from that anchor — zero additional wrong-token attempts
for the entire file walk and chat log (which also avoids the LB's
burst limit of 5 requests / 5 seconds; we additionally pace ~1.1s between
calls that cross that threshold).

## How I verified it

No Docker available in this sandbox (socket permission denied, no
passwordless sudo) — all 4 challenge services (`station_app.py` x4,
`lb_app.py`, `admin_app.py`) are plain Flask apps with no exotic deps
(`flask==3.0.3`, `requests==2.32.3`), so I ran them directly with
`python3`, reproducing every env var from `docker-compose.yml`
(`STATION_ID`, `TARGET_TIME`, `DEBUG_SEPARATOR`, `IS_RELAY_STATION`,
`ADMIN_RELAY_HOST`, `ADMIN_RELAY_URL`, `RELAY_KEY`, `FLAG`,
`STATION_URLS`, `REQUIRED_UA`) on localhost ports instead of the compose
network's service DNS names. Ran `solve_low_tide.py` against that live
stack twice; both runs printed the flag end-to-end straight from the
admin-relay's own JSON response (not read from `challenge.json` /
`docker-compose.yml`, which were only used to configure the local
reproduction's env vars and as a final sanity cross-check):
`CSAW{time_sensitive_scada_proxy_chain}`.

## Run it

```bash
python3 solve_low_tide.py http://<load-balancer-host>:<port>
# defaults to http://localhost:18080
```
