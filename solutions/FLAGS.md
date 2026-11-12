# CSAW 2026 Quals - misc

| category | challenge | flag | technique |
|---|---|---|---|
| misc | house_of_hollow_houses | `csaw{w4nd3r3r_0f_th3_h0ll0w_h0us3}` | robots.txt -> hidden letters -> base64 rite -> mirrored text -> poem "segment signature" cipher -> /sanctum/ (re-verified: solver rerun against a local copy of `chal/`) |
| misc | keep_walking_forward | `csaw{w4lk_b4_u_c4n_run(5p4c3)_3jfi9do9}` | DLL side-load + API-hash resolver (djb2 variant, cracked vs Wine export lists) -> pcap TLS1.2-GCM decrypt with keylog -> XOR key from AD domain -> Donut (Chaskey-CTR) -> ConfuserEx .NET (constants emulated statically) -> PowerShell builds the real flag in an unprinted variable; both handout "AI detection" flags are decoys planted in the sample |
| misc | 12345678 | **not solved** (3 of 4 fragments: `1n_0rd3r_`, `2_5t3@1_`, `u_n33d_`) | see `misc/BLOCKER_12345678.md` |
