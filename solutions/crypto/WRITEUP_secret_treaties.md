# secret_treaties (crypto)

**Flag:** `csaw{LLL_turns_kn4ps4cks_1nt0_p4nc4k3s_wh3n_d3ns1ty_1s_l0w}`

## Vulnerability
Flag is encrypted in 72-bit blocks as a plain subset sum over a 72-element public key (Merkle-Hellman style).
The key's density (72 / log2(max a) ~ 0.75) is well below the ~0.9408 CJLOSS bound, so the subset-sum instance
is solvable with lattice reduction; the trapdoor is never needed.

## Technique
CJLOSS lattice (x2-scaled to stay integral): rows `2*e_i || 2W*a_i` and `1...1 || 2W*c`. The target vector
`(1-2*bit_i)_i || 0` is very short (norm sqrt(72)); LLL surfaces it. +1 -> bit 0, -1 -> bit 1. Each recovered bit
vector is checked by re-summing the public key against the ciphertext. Block bits are packed MSB-first to bytes.
Solver uses a pure-Python exact-integer LLL (no fpylll needed).

## Run
```
python3 solve_secret_treaties.py [DATA_DIR]   # default ./secret_treaties_data (pubkey.txt, ciphertext.txt)
```

## Verification
Ran the solver in this session; every block's subset sum was checked against its ciphertext inside the solver,
output decoded to the flag above (<1s). Matches challenge.json's flag (cross-check only, after derivation).
