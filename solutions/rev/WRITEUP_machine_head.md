# Machine Head (rev)

**Flag:** `csaw{cl1mb1ng_th3_v1rtu4l_st4ck_0n3_0pc0d3_4t_4_t1m3}`

## Vuln / technique
`masterkey` is a bytecode VM: x86 is only the interpreter, `program[]` (3-byte instructions
`[op][a][b]`, 8 byte registers) is the checker. Opcodes: 0x91 VLD, 0x7A VXORI, 0x24 VADDI,
0x1D VMULI, 0xB2 VROL, 0x4E VXORR, 0x6D VADDR, 0xA7 VCMP, 0xE0 VHLT. Per input byte i the program
transforms it (xor/add/rol/xor/mul), XORs in a running state r1, compares to a target, then folds
the byte into r1 (`r1 = rol8(r1 + c, 3) ^ 0x9e`, seed 0x3C). Byte i's check depends on bytes 0..i-1,
so it is solved strictly left to right: carve the bytecode out of the binary (longest run of valid
3-byte instructions ending in VHLT), emulate, and for each position pick the unique byte (asserted
unique) whose VCMP passes.

## Run
`python3 solve_machine_head.py` (bundled `machine_head/masterkey`).

## Verification
Fed the recovered flag to the real binary (host aarch64 -> `qemu-x86_64 -L <amd64 glibc root> ./masterkey FLAG`):
`Correct! That's the master key.`; flipping the last char gives `Wrong.`. The author solve.py was also run
and produced the same flag; my solver's own carve+emulation reproduces it independently.
