# web/golf_heist

**Flag:** `csaw{el3gant_sw1ng_n3ver_c4ught}`

## Vulnerability

Two chained issues:

1. **Information disclosure via "teapot" responses.** `/pro-shop/inventory/{clubs,balls,bags}`
   each return `418 I'm a teapot` with an `X-Golf-Hint` header containing
   `base64("{rotor:06d}")` for one of three Enigma rotor offsets.
2. **Trusted-header privilege escalation (CVE GHSA-7r4p-vjf4-gxv4).** The
   Caddy reverse proxy's `forward_auth` config (`/api/engineer/caddyfile`)
   uses `copy_headers X-User-Id X-User-Role` but never *strips* those
   headers from the original client request before forwarding to the
   `/auth` micro-service. A client can simply set `X-User-Role: admin`
   itself; the backend (`/api/vault/admin-item`) blindly trusts whatever
   value arrives in that header with no real authentication, so the
   "trusted" auth-service-only header is attacker-controlled.

## Chain

1. Hit the three `/pro-shop/inventory/*` 418 endpoints, base64-decode
   `X-Golf-Hint` → three rotor offsets `r1, r2, r3`.
2. POST those offsets to `/api/enigma/encode` (same Enigma-style cipher
   the server runs internally on the string `"GOL"`) → 3 letters.
3. `/api/word-table` exposes the letter → word-synonym table used to
   build the vault passphrase (3 synonyms per letter, 27 combinations).
   Brute-force those 27 phrases against `POST /api/vault/enter` until one
   is accepted ("privileged" tier, but the special item stays locked).
4. The vault's privileged response links CVE `GHSA-7r4p-vjf4-gxv4`. Reading
   the PoC/advisory text embedded in the app's own hints shows the fix is
   to send `X-User-Role: admin` directly — the reverse proxy forwards it
   unstripped.
5. POST the *same* accepted phrase to `/api/vault/admin-item` with header
   `X-User-Role: admin` → `{"success": true, "tier": "admin", "flag": "csaw{el3gant_sw1ng_n3ver_c4ught}", ...}`.

## How I verified it

- Built the challenge's own Docker image (`Dockerfile` + pinned
  `requirements.txt`, no modifications needed) and ran it locally on
  `ctfnet` (`docker build -t golf_heist . && docker run -d --name golf_heist
  --network ctfnet -p 18000:8000 golf_heist`).
- Ran `solve_golf_heist.py localhost 18000` against the live container.
  It performs every step above purely through the HTTP API (no source
  inspection needed at solve time — it fetches `/api/word-table` and
  brute-forces the phrase rather than hardcoding the synonym index), and
  the service itself returned the flag in its JSON response:
  `csaw{el3gant_sw1ng_n3ver_c4ught}`, matching the value baked into
  `app/main.py`'s `FLAG` constant.

## Run it

```bash
python3 solve_golf_heist.py <host> <port>   # defaults to localhost:8000
```
