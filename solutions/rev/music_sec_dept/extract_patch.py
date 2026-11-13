"""Extract the Pd payload from the original ELF; constants traced to its loader."""
from pathlib import Path
import struct,hashlib

def extract(elf):
 data=Path(elf).read_bytes()
 assert data[:6]==b'\x7fELF\x02\x01'
 # Ghidra 0x1042f2 is virtual address 0x42f2 with its 0x100000 image base.
 address=0x42f2;size=0x1e14f
 phoff=struct.unpack_from('<Q',data,32)[0]
 phentsize,phnum=struct.unpack_from('<HH',data,54)
 for n in range(phnum):
  typ,flags,off,vaddr,paddr,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',data,phoff+n*phentsize)
  if typ==1 and vaddr<=address and address+size<=vaddr+filesz:
   blob=data[off+address-vaddr:off+address-vaddr+size];break
 else:raise ValueError('Encrypted payload not mapped')
 s0=0xf7d0d0f2^0xc7584227;s1=0x2afde2ac^0xda50826f;out=bytearray()
 for b in blob:
  s0=(s0*0xae3cd2f1+0x53a9be17)&0xffffffff
  s1^=(s1<<11)&0xffffffff;s1^=s1>>19;s1^=(s1<<8)&0xffffffff
  rot=((s1<<13)|(s1>>19))&0xffffffff
  k=(((rot^s0)*0x9b1d8e37)&0xffffffff)>>24
  out.append(b^k)
 return bytes(out)

if __name__=='__main__':
 import sys
 patch=extract(sys.argv[1]);Path(sys.argv[2]).write_bytes(patch)
 print('Extracted patch SHA256:',hashlib.sha256(patch).hexdigest())
