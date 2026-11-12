# hemispheres

**Flag:** `csaw{0n3_f1l3_tw0_truth5_p0lygl0t_m4g1c}`

Run: `pip install pillow; python3 solve_hemispheres.py [hemispheres_the_signal.png]`

## Technique
- File is a PNG (read front-to-back) with a ZIP appended after IEND (326 bytes starting `PK\x03\x04`); zip readers find the EOCD from EOF, so it is a PNG||ZIP polyglot.
- `flag.txt` in the ZIP is password-protected (ZipCrypto).
- Password is in the blue-channel LSBs, row-major: 16-bit big-endian length, then that many bytes -> `r3ad_b3tw33n_th3_p1x3ls`.
- Decrypt with `zipfile` using that password.

## Verification
Ran solver in this session; flag derived from the image itself (author's challenge.json not consulted as source).
