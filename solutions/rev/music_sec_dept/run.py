"""One-command artifact-derived recovery, checkpoint test, and full VM replay."""
from pathlib import Path
import hashlib,json
from extract_patch import extract
from emulator import VM,ART
from solve import solve

here=Path(__file__).parent
decoded=extract(ART/'csirac.pd_linux')
assert decoded==(ART/'hidden_patch.pd').read_bytes(),'Extracted patch mismatch'
print('Original ELF -> Pd patch verified:',hashlib.sha256(decoded).hexdigest())
base=['CUE IKOW[g','SYNC',"EQ music'_'"]
checkpoint=VM();checkpoint.run(breakpc=0x212)
for command in base+['KEY M4ch1n3_K3y!','EXPORT 9a3f']:checkpoint.feed(command+'\n')
reference="L7USw*KLz'0VI/3)keO#]_}z\":M$tYIFf-HB'c8NwU"
assert reference.encode() in checkpoint.out,'Independent checkpoint mismatch'
print('Full independently captured 42-byte checkpoint matched.')
result=solve('9a3f......')
chosen=result['suffix_candidates'][0]
print('Selected by generic alphabet score, not by target-string equality.')
replay=VM();replay.run(breakpc=0x212)
commands=base+['KEY '+chosen['key'],'EXPORT '+result['export_argument']]
for command in commands:replay.feed(command+'\n')
assert chosen['text'].encode() in replay.out
(here/'fresh_replay.txt').write_bytes(replay.out)
print('\nFULL FIRMWARE REPLAY:\n'+replay.out.decode('latin1'))
