#!/usr/bin/env python3
"""Native Purr-Data validation using an in-process console transport adapter.

The original patch's one netreceive object is replaced with an abstraction of
the same inlet/outlet shape. It delivers one raw byte per event and records
each send byte. All ROM, computation, and original clock ordering are retained.
"""
import argparse,hashlib,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parent
ART=pathlib.Path('/Users/ashmit/Desktop/challenge-repo/2026/CSAW-Quals/rev/music_sec_dept/csirac')
ENGINE='/Applications/Purr-Data.app/Contents/Resources/app.nw/bin/pd-l2ork'
CYCLONE='/Applications/Purr-Data.app/Contents/Resources/app.nw/extra/cyclone'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--tag',default='checkpoint');ap.add_argument('--candidate');ap.add_argument('--key',default='M4ch1n3_K3y!');ap.add_argument('--export',dest='arg',default='9a3f');args=ap.parse_args()
 if args.candidate:
  record=json.loads(pathlib.Path(args.candidate).read_text());args.key=record['suffix_candidates'][0]['key'];args.arg=record['export_argument']
 commands=['CUE IKOW[g','SYNC',"EQ music'_'",'KEY '+args.key,'DECK','EXPORT '+args.arg]
 work=ROOT/'native_runs'/args.tag;work.mkdir(parents=True,exist_ok=True)
 original=(ART/'hidden_patch.pd').read_text()
 assert original.count('netreceive -b 4562')==1
 (work/'engine_patch.pd').write_text(original.replace('netreceive -b 4562','local_transport'))
 # Native byte-level transport: same local input buffering and same output path.
 transport='''#N canvas 0 0 800 600 12;
#X obj 20 20 inlet;
#X obj 20 50 route send;
#X obj 20 80 t f f;
#X obj 20 110 print NATIVE_BYTE;
#X obj 240 20 r native_input;
#X obj 240 50 outlet;
#X obj 400 20 loadbang;
#X msg 400 50 1;
#X obj 400 80 outlet;
#X obj 100 150 t f b;
#X obj 200 180 f 0;
#X obj 100 220 expr if($f1 == if($f2 == 0 \\, 67 \\, if($f2 == 1 \\, 83 \\, if($f2 == 2 \\, 73 \\, if($f2 == 3 \\, 82 \\, if($f2 == 4 \\, 65 \\, if($f2 == 5 \\, 67 \\, 62)))))) \\, $f2+1 \\, if($f1 == 67 \\, 1 \\, 0));
#X obj 100 260 t f f;
#X obj 100 290 sel 7;
#X obj 100 320 t b b;
#X msg 180 350 0;
#X obj 100 390 s native_prompt;
#X connect 0 0 1 0;
#X connect 1 0 2 0;
#X connect 2 0 9 0;
#X connect 2 1 3 0;
#X connect 4 0 5 0;
#X connect 6 0 7 0;
#X connect 7 0 8 0;
#X connect 9 0 11 0;
#X connect 9 1 10 0;
#X connect 10 0 11 1;
#X connect 11 0 12 0;
#X connect 12 0 13 0;
#X connect 12 1 10 1;
#X connect 13 0 14 0;
#X connect 14 0 16 0;
#X connect 14 1 15 0;
#X connect 15 0 10 1;
'''
 (work/'local_transport.pd').write_text(transport)
 nodes=['loadbang','del 300','1','metro 0.1','t b b b','\\; cuec execute \\;','\\; headc step \\;','\\; headc out \\;','r native_prompt','del 0','f 0','t f f','+ 1','sel 0 1 2 3 4 5 6 7','s native_input','del 100','\\; pd quit']
 messages={2,5,6,7,16}
 lines=['#N canvas 0 0 800 800 12;']
 for i,node in enumerate(nodes):lines.append('#X %s 20 %d %s;' % ('msg' if i in messages else 'obj',20+i*25,node))
 for c in commands:lines.append('#X msg 400 100 '+ ' \\, '.join(str(b) for b in (c+'\n').encode())+';')
 edges=[(0,0,1,0),(1,0,2,0),(2,0,3,0),(3,0,4,0),(4,0,5,0),(4,1,6,0),(4,2,7,0),(8,0,9,0),(9,0,10,0),(10,0,11,0),(11,0,13,0),(11,1,12,0),(12,0,10,1),(13,6,15,0),(15,0,16,0)]
 for i in range(len(commands)):edges.extend([(13,i,17+i,0),(17+i,0,14,0)])
 for a,b,c,d in edges:lines.append(f'#X connect {a} {b} {c} {d};')
 (work/'controller.pd').write_text('\n'.join(lines)+'\n')
 cmd=[ENGINE,'-unique','-noprefs','-nogui','-noaudio','-nomidi','-stderr','-path',CYCLONE,'-path',str(ART),'-path',str(work),'-open',str(work/'engine_patch.pd'),'-open',str(work/'controller.pd')]
 p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=work)
 try: log,_=p.communicate(timeout=35)
 except subprocess.TimeoutExpired:
  p.terminate();log,_=p.communicate(timeout=3)
 (work/'engine.log').write_bytes(log)
 raw=bytes(int(v)&255 for v in re.findall(rb'NATIVE_BYTE: ([0-9]+)',log))
 (work/'raw_response.bin').write_bytes(raw)
 print(raw.decode('latin1'),flush=True)
 errors=[s for s in log.decode(errors='replace').splitlines() if s.startswith('error:') or 'couldn' in s]
 result={'engine':'native Purr-Data 2.20.1','exit_code':p.returncode,'commands':commands,'transport_adapter':True,'original_patch_sha256':hashlib.sha256(original.encode()).hexdigest(),'rom_sha256':hashlib.sha256((ART/'session.bin').read_bytes()).hexdigest(),'response_hex':raw.hex(),'response':raw.decode('latin1'),'errors':errors}
 (work/'result.json').write_text(json.dumps(result,indent=2))
 if errors:print('ENGINE_ERRORS',errors)
 if 'rendering stem' not in result['response']:raise SystemExit('No native render captured')

if __name__=='__main__':main()
