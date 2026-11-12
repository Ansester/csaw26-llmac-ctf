# taking_on_the_temple / "Midnight Vault" (crypto)

**Flag:** `csaw{tH3_c0fF3r_w4s_n3v3r_th3_gU4rd1an}`

## Structure
Flask app with 4 gated stages; artifacts are only downloadable once the previous stage is accepted.
Each stage is a homemade layered cipher with a "mirrored chunks" transposition:
1. **Granite** - braille `STONE` = autokey primer; ciphertext copied in reversed *trios*. Plaintext ends `MARKER GRANITE`
   - the numeric suffix is NOT in the plaintext; it must come from the "other markings" list, which contains decoys
   (`Q0hFQ0tTVU1fRkFJTF9OT1RfS0VZ` = base64 "CHECKSUM_FAIL_NOT_KEY", `checksum: 7f1a0d`, `LOCK / 04 / 19 / 71`).
   The solver tries `GRANITE-<n>` for each number in the markings and lets the server decide -> `GRANITE-71`.
2. **Frost** - `frost.bin` is reversed in 8-byte blocks, then XOR with a SHA-256 counter stream keyed by sha256(k1). Plaintext carries `MARKER: CRYO-29`.
3. **Iron** - key = hash chain h0=sha256(k2), h1=sha256(h0||k1), h2=sha256(rev(h1)||k2); payload b64 reversed in quartets. Gives `FERRUM-83`.
4. **Vault** - AES-256-GCM, key = sha256(k1|k2|k3), nonce/ciphertext b64 with mirrored quartets, AAD from json. GCM tag verification
   confirms all three markers are exactly right; decrypts to the flag.

## Run
```
python solve_taking_on_the_temple.py HOST PORT
```

## Verification
Ran `app.py` locally (port 5001 since 5000 was busy) and ran the solver: each stage accepted by the server, the vault POST
returned "THE VAULT IS OPEN", GCM tag verified. Did not use the reference's hardcoded markers (solver derives/tests them).
Flag matches challenge.json (cross-check only).
