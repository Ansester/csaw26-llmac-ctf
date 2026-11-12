# polly (crypto)

**Flag:** `csaw{Am4Z3s_m3_thE_W1lL_0f_1nst1nct}`

## Vulnerability
The server derives a 64-bit xorshift-style state `seed` and ChaCha20-encrypts the flag with a nonce
`base_nonce(9 bytes) || (state_at(flag_x, seed) & 0xFFFFFF)`. The xorshift transform is **linear over GF(2)**, and
the shift parameters/direction are derived from the public nonce prefix (`shake_256(nonce[:9])`). The service
also leaks the low byte of `state_at(x, seed)` for an attacker-chosen `x`.

## Technique
1. Compute shifts/direction from the nonce prefix.
2. Query x = 0,1,2,... and collect the leaked low byte; each bit is a GF(2)-linear equation in the 64 seed bits
   (track T^x applied to each basis vector). Rank hits 64 after ~9 queries; Gaussian-eliminate to recover the seed.
3. Validate with one extra, unused query.
4. Iterate the generator (x < 2^24) until the low 24 bits equal the nonce suffix -> `flag_x`.
5. Ask the oracle for x = flag_x with an empty message: it returns ChaCha20 keystream XOR; XOR with the
   encrypted flag to decrypt (same keystream since nonce is identical).

## Run
```
python solve_polly.py HOST PORT      # needs pwntools
```

## Verification
No docker permission on this host, so I served `deployment/main.py` with `socat TCP-LISTEN:5000,fork EXEC:python3 -u main.py`
(identical to the Dockerfile CMD). Ran with a random placeholder FLAG -> solver returned the placeholder (proves real recovery);
ran with the repo's configured FLAG -> output matched the repo's value (cross-check only, run after derivation).
