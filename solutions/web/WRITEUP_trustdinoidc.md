# web/trustdinoidc

**Flag:** `csaw{str4ta_sk1pped_th3_p1n}`

## Architecture

OIDC-style SSO demo: three services.

- `trustdinoidc` (`main.py`, port 8990, public) — the dino-poster portal.
  Trusts two issuers: `paleoid.example.com` and `strataid.example.com`.
- `paleoid` (`idp.py`, internal) — one of the two IdPs.
- `strataid` (`idp.py`, internal) — the other IdP; **same code**, just a
  different `ISSUER`/`ACCENT` env var.

Both IdPs mint self-signed RS256 JWT `id_token`s on `/authorize` and expose
their public key/cert via `/jwks.json`. `main.py` does NOT use the JWKS
endpoint to validate every incoming token's signature at verify-time —
instead it does a one-time `fetch_pin()` **only for `paleoid`** at process
boot, caching that one issuer's certificate fingerprint in
`PINNED_CERTS = {"paleoid.example.com": fetch_pin("paleoid")}`.

## Vulnerability

`verify()` in `main.py`:

```python
def verify(token):
    header = pyjwt.get_unverified_header(token)
    claims = pyjwt.decode(token, options={"verify_signature": False})
    iss = claims.get("iss")
    if iss not in ALLOWED_ISSUERS:
        raise ValueError("unknown issuer")
    cert = x509.load_der_x509_certificate(base64.b64decode(header["x5c"][0]))
    pin = PINNED_CERTS.get(iss)
    if pin and cert.fingerprint(hashes.SHA256()) != pin:
        raise ValueError("certificate mismatch")
    return pyjwt.decode(token, key=cert.public_key(), algorithms=["RS256"], ...)
```

Both `paleoid.example.com` and `strataid.example.com` are in
`ALLOWED_ISSUERS`, but `PINNED_CERTS` only has an entry for `paleoid`.
`pin = PINNED_CERTS.get(iss)` is `None` for `strataid`, so
`if pin and ...` short-circuits — the certificate-mismatch check is
**skipped entirely** for strataid tokens. The actual signature check at
the bottom then uses whatever public key is embedded in the token's own
`x5c` JWT header, i.e. the attacker's own self-signed cert. In other
words: for `strataid`, the "signature verification" verifies a token
against a key the attacker supplied in the very same token — it proves
nothing.

`paleoid` is correctly protected because its cert is pinned from its own
JWKS at boot, so a forged token (self-signed key, but claiming
`iss: paleoid.example.com`) fails the fingerprint check.

## Exploit

1. Generate a throwaway 2048-bit RSA key + self-signed X.509 cert.
2. Craft an `id_token` JWT: `iss: strataid.example.com`,
   `aud: trustdinoidc-portal`, `scope: openid profile flagosaurus:redeem`
   (the admin-only scope — `ADMIN_SCOPE = "flagosaurus:redeem"` in
   `main.py`), sign it RS256 with the throwaway key, and put the
   throwaway cert's DER bytes (base64) in the JWT header's `x5c`.
3. `POST /oauth/callback` with `id_token=<forged>` — `verify()` accepts it
   (no pin for strataid) and sets it as the `session` cookie.
4. `GET /` — `ADMIN_SCOPE in scope` is now true, so `index()` renders the
   Flagosaurus section with `flag=FLAG`.
5. (Sanity control, included in the solver): the identical forge attempt
   with `iss: paleoid.example.com` instead is rejected with
   `401 certificate mismatch`, confirming the asymmetry is real and
   specific to strataid's missing pin.

## How I verified it

Ran all three services directly with `python3` (plain Flask apps, deps
`flask`/`pyjwt`/`cryptography` — no Docker available in this sandbox,
socket permission denied, no passwordless sudo): `idp.py` twice as
`paleoid.example.com` (port 8991) and `strataid.example.com` (port 8992),
and `main.py` (port 8990, `FLAG=csaw{str4ta_sk1pped_th3_p1n}`). `main.py`
resolves its two IdPs by Docker Compose service name (`paleoid`,
`strataid`); I pointed those lookups at `127.0.0.1:<port>` instead to
reproduce the compose network locally (same two IdP processes,
same logic, just no DNS).

Ran `solve_trustdinoidc.py 127.0.0.1 8990` against that live stack. It:
confirmed the paleoid forgery is rejected (`401 certificate mismatch`),
then forged and submitted the strataid token, fetched `/`, and extracted
the flag straight from the rendered HTML (not read from `challenge.json`,
which was only used as a final sanity cross-check):
`csaw{str4ta_sk1pped_th3_p1n}`.

## Run it

```bash
python3 solve_trustdinoidc.py <host> <port>   # defaults to localhost:8990
```
