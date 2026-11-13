"""Answer-agnostic recovery: constrain only public csaw{ prefix and final }.
All 48-bit state choices consistent with those symbols are retained. Ranking
uses only a general flag alphabet preference (letters/digits/underscore).
"""
from emulator import VM,ROM
from itertools import product
from pathlib import Path
import json,string
HERE=Path(__file__).parent

def checkpoint(export):
 v=VM();v.run(breakpc=0x212)
 for c in ['CUE IKOW[g','SYNC',"EQ music'_'",'KEY 000000000000']:v.feed(c+'\n')
 v.q.extend(('EXPORT '+export+'\n').encode());v.run(breakpc=0x1026-248)
 return v

def transform(s):
 s=list(s)
 for order,mul,add in [(range(6),0x8d,0x3b),(range(5,-1,-1),0x4f,0xc7)]*2:
  prev=0
  for i in order:s[i]=((s[i]^prev)*mul+add)&255;prev=s[i]
 return s

def inverse(s):
 s=list(s)
 for order,mul,add in [(range(5,-1,-1),0x4f,0xc7),(range(6),0x8d,0x3b)]*2:
  old=s[:];prev=0;inv=pow(mul,-1,256)
  for i in order:s[i]=(((old[i]-add)*inv)&255)^prev;prev=old[i]
 return s

def output(s,q):
 s=list(s);gen=s[:]
 for n in range(36,0,-1):
  t=((s[5]+s[0])&255)^s[2];t=(t+s[4])&255;t=(t*0x67)&255;t^=t>>3;t^=s[1];t=(t+s[3])&255;t^=n;t=(t+0x9e)&255
  s=s[1:]+[t];gen.append(t)
 return ''.join(chr(32+(((g+(ROM[0x8c+(5*i)%42]^q[i%6]))&255)%95)) for i,g in enumerate(gen))

def rank(s):
 inner=s[5:-1]
 return sum(3 if c.isalpha() else 2 if c.isdigit() else 3 if c=='_' else -7 for c in inner)

def solve(arg):
 v=checkpoint(arg);q=v.m[0x85:0x8b];s=v.m[0x34:0x3a]
 assert transform(q)==s,(q,s,transform(q))
 expected=output(s,q)
 before=len(v.out);v.run(breakpc=0x212)
 assert expected in v.out[before:].decode('latin1')
 choices=[]
 for i,c in enumerate('csaw{'):
  tap=ROM[0x8c+(5*i)%42]^q[i%6]
  choices.append([x for x in range(256) if 32+(((x+tap)&255)%95)==ord(c)])
 choices.append(range(256));all_candidates=[];suffix=[]
 for state in product(*choices):
  plain=output(state,q);key=bytes(a^b for a,b in zip(inverse(state),q)).hex();entry={'key':key,'state':bytes(state).hex(),'text':plain,'score':rank(plain)};all_candidates.append(entry)
  if plain.endswith('}'):suffix.append(entry)
 suffix.sort(key=lambda x:(-x['score'],x['key']))
 name=arg.replace('.','_')
 result={'export_argument':arg,'q':bytes(q).hex(),'neutral_state':bytes(s).hex(),'neutral_output':expected,'prefix_choices':[list(c) if i<5 else 'all 256' for i,c in enumerate(choices)],'prefix_count':len(all_candidates),'suffix_count':len(suffix),'suffix_candidates':suffix}
 (HERE/f'recovery_{name}.json').write_text(json.dumps(result,indent=2));(HERE/f'all_prefix_{name}.json').write_text(json.dumps(all_candidates))
 print(json.dumps({k:v for k,v in result.items() if k!='suffix_candidates'},indent=2));print(json.dumps(suffix[:10],indent=2))
 return result
if __name__=='__main__':
 import sys
 for arg in sys.argv[1:] or ['9a3f','9a3f......']:solve(arg)
