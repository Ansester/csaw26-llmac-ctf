"""Independent emulator derived only from hidden_patch.pd and session.bin."""
from pathlib import Path
from collections import deque, Counter
import json, argparse, os
ART=Path(os.environ.get('CSIRAC_ARTIFACTS',str(Path(__file__).parent/'artifacts')))
if not ART.exists(): ART=Path('/Users/ashmit/Desktop/challenge-repo/2026/CSAW-Quals/rev/music_sec_dept/csirac')
ROM=(ART/'session.bin').read_bytes()
class VM:
 def __init__(self):
  self.m=list(ROM[:248])+[0]*8; self.m[249]=248
  self.code=ROM[248:]; self.r=[0]*4; self.pc=0; self.pred=False; self.halt=False
  self.q=deque(); self.out=bytearray();self.steps=0;self.hist=Counter();self.trace=[]
 def read(self,a):
  a&=255
  if a==253:
   v=self.q.popleft() if self.q else 0;self.m[253]=v;return v
  if a==254:
   v=len(self.q)&255;self.m[254]=v;return v
  return self.m[a]
 def write(self,a,v):
  a&=255;v&=255;self.m[a]=v
  if a==255:self.out.append(v)
 def alu(self,k,a,b):
  if k==0:v=a+b
  elif k==1:v=a-b
  elif k==2:v=a*b
  elif k==3:v=int(a/b) if b else 0
  elif k==4:v=a&b
  elif k==5:v=a^b
  elif k==6:v=a>>(b&7)
  elif k==7:v=a<<(b&7)
  elif k==8:v=a|b
  elif k==9:v=a%b if b else 0
  else:raise ValueError(('alu',k))
  return v&255
 def push(self,v):
  p=(self.read(249)-1)&255;self.write(249,p);self.write(p,v)
 def pop(self):
  p=self.read(249);v=self.read(p);self.write(p,0);self.write(249,(self.read(249)+1)&255);return v
 def step(self):
  pc=self.pc;a,b=self.code[pc:pc+2];self.pc=(pc+2)&4095
  o=a>>4;x=a&15;rx=x>>2;mode=x&3;self.hist[o]+=1;self.steps+=1
  if o==0:
   if x==1:
    hi=self.pop();lo=self.pop();self.pc=((hi&15)<<8)|lo
   elif x in (2,3):self.halt=True
  elif o in (1,2):self.r[mode]=self.alu(rx+(4 if o==2 else 0),self.r[mode],b)
  elif o==3:
   d=b>>6;s=(b>>4)&3;self.r[d]=self.alu(x,self.r[d],self.r[s])
  elif o in (4,5):
   if mode==0:
    if o==4:self.r[rx]=b
    else:self.r[b&3]=self.r[rx]
   else:
    reg=b&3;upd=(b>>2)&3
    address=self.r[reg] if mode==1 else (b if mode==2 else self.read(b))
    if o==4:self.r[rx]=self.read(address)
    else:self.write(address,self.r[rx])
    if mode==1 and upd in (1,2):self.r[reg]=(self.r[reg]+(1 if upd==1 else -1))&255
  elif o in (6,7):
   lhs=self.r[mode];rhs=b if o==6 else self.r[b&3]
   self.pred=[lhs==rhs,lhs!=rhs,lhs>rhs,lhs>=rhs][rx]
  elif o==8:
   if mode==0:self.write(248,b)
   elif mode in (1,2):
    self.write(self.read(248),b)
    if mode==2:self.write(248,(self.read(248)+1)&255)
  elif o==9:
   if x==0:self.push(self.r[b&3])
   elif x==1:self.r[b&3]=self.pop()
   elif x==2:self.push(b)
  elif o in (10,11):pass
  elif o in (12,13,14,15):
   dest=(x<<8)|b
   if o==15:
    ret=self.pc;self.push(ret&255);self.push(ret>>8);self.pc=dest
   elif o==12 or (o==13 and self.pred) or (o==14 and not self.pred):self.pc=dest
 def run(self,limit=1000000,breakpc=None):
  for _ in range(limit):
   if self.halt or (breakpc is not None and self.pc==breakpc):return
   self.step()
  raise RuntimeError(f'step limit pc={self.pc:03x} out={bytes(self.out)!r}')
 def feed(self,s,limit=200000):
  self.q.extend(s.encode() if isinstance(s,str) else s)
  for _ in range(limit):
   self.step()
   # input loop at code 0x1a checks length repeatedly; permit finish output
   if not self.q and self.pc==0x212:return
  raise RuntimeError(f'feed limit pc={self.pc:03x} out={bytes(self.out)!r}')
 def state(self):return {'pc':hex(self.pc),'registers':self.r,'pb34_39':bytes(self.m[0x34:0x3a]).hex(),'pb85_8a':bytes(self.m[0x85:0x8b]).hex(),'key':bytes(self.m[0x18:0x1e]).hex(),'out':bytes(self.out).decode('latin1'),'steps':self.steps,'q':list(self.q)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--commands',nargs='*',default=['CUE IKOW[g','SYNC',"EQ music'_'",'KEY 000000000000','EXPORT 9a3f']);args=p.parse_args()
 v=VM()
 try:
  v.run(100000,breakpc=0x212);print('BOOT',json.dumps(v.state()))
  for c in args.commands:
   v.feed(c+'\n');print(c,json.dumps(v.state()))
 except Exception as e:print(type(e).__name__,e, v.state());raise
