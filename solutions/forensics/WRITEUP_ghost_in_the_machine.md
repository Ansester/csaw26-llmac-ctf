# ghost_in_the_machine

**Flag:** `csaw{t1m1ng_1s_3v3ryth1ng_1n_th3_s1l3nt_ch4nn3l}`

Run: `python3 solve_ghost_in_the_machine.py [ghost_capture.pcap]` (bundled pcap is the default).

## Technique
- 504 identical UDP `PING` packets: content is useless; data is in inter-arrival timing.
- TTL histogram from the pcap itself: 385 packets TTL 64 (real), 119 packets TTL 113 (decoys). Solver takes the majority TTL as the carrier and drops the rest.
- Gaps between consecutive real packets are bimodal (~50 ms = 0, ~150 ms = 1); threshold at midpoint, MSB-first, 8 bits/byte -> 48 ciphertext bytes.
- Key is in UDP source port: `key_byte = sport - 40000`; stream is `sh4dow` repeated. XOR -> flag.

## Verification
Ran my own stdlib solver (modeled on author's reference) in this session; it printed the flag above. Matches challenge-info.md only as a post-hoc cross-check.
