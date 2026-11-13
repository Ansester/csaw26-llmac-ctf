# rev flags

| category | challenge | flag | technique |
|---|---|---|---|
| rev | autobahn | csaw{c0d3_th4t_rewr1t3s_1ts3lf_c4nt_b3_tru5t3d} | undo SMC XOR on `enccode`, derive keystream from decrypted code; confirmed by running the binary |
| rev | machine_head | csaw{cl1mb1ng_th3_v1rtu4l_st4ck_0n3_0pc0d3_4t_4_t1m3} | carve VM bytecode, emulate left-to-right; confirmed by the real binary printing "Correct!" |
| rev | music_sec_dept | csaw{~i_love_my_computer_&_it_loves_me~<3} | Pd-patch/session.bin ROM VM; EXPORT render = nonlinear NLFSR keystream folded mod-95; recover 12-hex KEY by answer-agnostic public-prefix state inversion (12288 states -> 87 end in }, flag ranks #1), replayed through an independent decoy-validated emulator |
