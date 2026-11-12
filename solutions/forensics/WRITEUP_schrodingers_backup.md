# schrodingers_backup

**Flag:** `csaw{th3_c4t_c0mm1tt3d_but_th3_j0urn4l_r3m3mb3r5}`

Run: `pip install cryptography; python3 solve_schrodingers_backup.py [schrodingers_evidence.zip]`

## Technique
- Final DB is disarmed and shows only the last display shares; the history lives in the uncheckpointed `catalog.db-wal`.
- Own WAL parser: validates header checksum, both salts and cumulative frame checksums; a frame with `commit_size != 0` ends a transaction and makes all pending pages visible. Parsing stops at the first invalid frame.
  - Frames 35-37 are valid but uncommitted (discarded); frame 37+ carries a stale-generation salt (decoy commit marker, rejected).
- Result: 28 committed snapshots. Each snapshot is loaded in memory (`sqlite3.deserialize`, header bytes 18-19 set to rollback mode) — original files never opened by sqlite.
- For each snapshot with `control.armed=1` (20 visits, repeats kept) token = north.share XOR south.share.
- key = SHA-256(DOMAIN || tokens), AES-256-GCM decrypt `capsule.json` with DOMAIN as AAD.

## Verification
GCM tag authenticates only for the exact correct history, so successful decryption is self-verifying. Ran in this session; output matches.
