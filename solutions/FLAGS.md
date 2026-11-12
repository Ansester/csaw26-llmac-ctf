# CSAW 2026 Quals - crypto

| category | challenge | flag / answer | technique |
|---|---|---|---|
| crypto | polly | `csaw{Am4Z3s_m3_thE_W1lL_0f_1nst1nct}` | Linear GF(2) xorshift: leak low byte for x=0..8, Gaussian-eliminate to recover 64-bit seed, search x for nonce suffix, XOR oracle keystream with encrypted flag |
| crypto | secret_treaties | `csaw{LLL_turns_kn4ps4cks_1nt0_p4nc4k3s_wh3n_d3ns1ty_1s_l0w}` | Low-density subset-sum (CJLOSS lattice + exact-integer LLL) per 72-bit block |
| crypto | taking_on_the_temple | `csaw{tH3_c0fF3r_w4s_n3v3r_th3_gU4rd1an}` | 4-stage layered ciphers (autokey, SHA-256 streams, mirrored chunks); decoy-laden Granite suffix resolved by server oracle; AES-GCM tag verifies final key |
| crypto | finders_keepers | `cantfindit` (plaintext, no wrapper); metadata layer decrypts to `csaw{y0u_@lw@ys_kn0w_wh3r3_t0_l00k}` | Faint drifting base64 in video frames -> `cantfindit`; also Vigenere key for XMP blob. No oracle available - see WRITEUP |

Verification notes: polly verified live (local socat instance, random + real FLAG); taking_on_the_temple verified against a local Flask instance
(server accepted each stage, vault opened); secret_treaties verified by re-summing subset sums; finders_keepers has no service, answer derived from artifact.
No docker permission on this host, so services were run directly (same commands as Dockerfile CMD / app entrypoint).
