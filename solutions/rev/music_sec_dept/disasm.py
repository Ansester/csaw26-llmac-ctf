from emulator import ROM
N=['a','b','c','d'];OPS=['add','sub','mul','div','and','xor','shr','shl','or','mod'];CMP=['eq','ne','gt','ge']
def dis(pc):
 a,b=ROM[pc:pc+2];o=a>>4;x=a&15;r=x>>2;m=x&3
 if o==0:s={0:'nop',1:'ret',2:'halt',3:'halt'}.get(x,'nop')
 elif o in (1,2):s=f'{OPS[r+(4 if o==2 else 0)]} {N[m]}, #{b:02x}'
 elif o==3:s=f'{OPS[x]} {N[b>>6]}, {N[(b>>4)&3]}'
 elif o in (4,5):
  v=f'#{b:02x}' if o==4 and m==0 else N[b&3] if m==0 else '['+(N[b&3]+{0:'',1:'++',2:'--',3:'?'}[(b>>2)&3] if m==1 else f'{b:02x}' if m==2 else f'[{b:02x}]')+']'
  s=f'load {N[r]}, {v}' if o==4 else f'store {v}, {N[r]}'
 elif o in (6,7):s=f'cmp.{CMP[r]} {N[m]}, '+(f'#{b:02x}' if o==6 else N[b&3])
 elif o==8:s=f'emit.{m} #{b:02x}'
 elif o==9:s=['push '+N[b&3],'pop '+N[b&3],f'push #{b:02x}'][x] if x<3 else 'nop'
 elif o in (10,11):s='nop'
 else:s=f'{["jmp","jt","jf","call"][o-12]} file {((x<<8)|b)+248:03x}'
 return f'{pc:04x}  {a:02x}{b:02x}  {s}'
if __name__=='__main__':
 import sys
 for i in range(int(sys.argv[1],16),int(sys.argv[2],16),2):print(dis(i))
