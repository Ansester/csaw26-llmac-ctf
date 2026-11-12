# Forensics flags (CSAW 2026 Quals)

| category | challenge | flag | technique |
|---|---|---|---|
| forensics | ghost_in_the_machine | `csaw{t1m1ng_1s_3v3ryth1ng_1n_th3_s1l3nt_ch4nn3l}` | Filter decoys by IP TTL, inter-packet gaps -> bits, XOR with key (`sh4dow`) from UDP src ports |
| forensics | hemispheres | `csaw{0n3_f1l3_tw0_truth5_p0lygl0t_m4g1c}` | PNG||ZIP polyglot; ZIP password from blue-channel LSB stego |
| forensics | schrodingers_backup | `csaw{th3_c4t_c0mm1tt3d_but_th3_j0urn4l_r3m3mb3r5}` | Replay committed SQLite WAL transactions (validate salts/checksums), XOR shares at armed commits, AES-GCM key |
| forensics | breach_zero_day | `csaw{RELAYSHELL_WINDEFEND_FORESTTIGER}` | Correlate monitoring gap (01:09:47) with pcap C2 start, WinDefend stop after Afd4Eop12 driver load, reversed memdump fragments |

All four solvers were run in-session and derived the flag from the artifacts. Backdoor-name selection in breach_zero_day is structural (no timestamps in memdump), see its writeup.
