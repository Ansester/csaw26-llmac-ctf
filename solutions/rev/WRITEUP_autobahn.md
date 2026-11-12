# Autobahn (rev)

**Flag:** `csaw{c0d3_th4t_rewr1t3s_1ts3lf_c4nt_b3_tru5t3d}` (password `n2o_boost`)

## Vuln / technique
`secret_check` lives in ELF section `enccode`, stored XOR-encrypted with the repeating
8-byte key `13 37 c0 de ba ad f0 0d`. `main` mprotects it RWX and XORs it in place before
calling it (self-modifying code). The password is built from `movb $imm,disp(%rbp)`
instructions. The flag keystream is derived from the *decrypted* code bytes:
`k[i] = (code[(7i+3) % L] + 5i + 0x6b) & 0xff`, and `enc_flag` in `.rodata` is XORed with it.

## Run
`python3 solve_autobahn.py` (uses bundled `autobahn/nitro`; pure Python, no execution)

## Verification
- Static: the solver reproduced the decrypt, recovered the password, and decrypted the flag.
- Dynamic (independent): ran the real binary (host is aarch64, so via `qemu-x86_64 -L <amd64 libc6 root>`):
  `./nitro n2o_boost` -> `NITRO ENGAGED: csaw{...}` (identical flag); a wrong password prints
  "Access denied". Note the shipped file lacks the exec bit; `chmod +x` a copy.
- Matches the `flag` in challenge.json (checked only after derivation).
