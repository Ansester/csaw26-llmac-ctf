# CSAW 2026 Quals - web

| category | challenge | flag | technique |
|---|---|---|---|
| web | flagchecker | `csaw{tim3_w4its_f0r_n0_0ne}` | timing side-channel on a `__eq__` that sleeps per matching leading char (armed by a crafted Chrome UA); recovered char-by-char with adaptive-sample-count min-timing, cross-checked against the live container's own `.env` |
| web | golf_heist | `csaw{el3gant_sw1ng_n3ver_c4ught}` | base64'd Enigma-rotor hints leaked via HTTP 418 -> brute-forced vault passphrase -> trusted `X-User-Role: admin` header (Caddy forward_auth header-stripping) |
| web | low_tide | `CSAW{time_sensitive_scada_proxy_chain}` | multi-stage pivot through forged per-station tokens, a VFS walk, a chat-log leak, to a hidden admin relay (flag is uppercase `CSAW{...}`, unlike the others) |
| web | trustdinoidc | `csaw{str4ta_sk1pped_th3_p1n}` | OIDC cert-pinning asymmetry: self-sign a cert, forge an `id_token` for the unpinned issuer with the admin scope |
| web | csale | `csaw{Th4t3_R0ugH_Bud1y}` | UNION SQLi leaks an XOR key + encrypted passwords; decrypt, log in, then an IDOR on the draft unlock/preview routes downloads another user's flag-bearing image |
| web | juggler | `csaw{tw0_f0r_0n3_2gc9w2hz}` | PHP mass-assignment + loose (`==`) type juggling: setting the session role to a bool satisfies `in_array` against the real admin-role strings |

## Decoys deliberately NOT submitted

- **csale**: a seeded "Flag" listing's `fulfillment_note` literally contains
  `csawctf{th1s_wAs_EZ}` (wrong prefix too) -- a honeypot, not the real flag.
