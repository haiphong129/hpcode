import os
cwd = os.path.dirname(os.path.abspath(__file__))
def readdata(fn):
    f = open(os.path.join(cwd,fn),"r")
    data = f.read().replace("\n\n","\n").split('\n')
    f.close()
    return data
def solve():
    dans = readdata("pass.ans")
    dinp = readdata("pass.inp")
    dout = readdata("pass.out")
    n,s = int(dinp[0]),dinp[1:]
    for i in range(n):
        ans = [int(x) for x in dans[i].split()]
        out = [int(x) for x in dout[i].split()]
        for x in out:
            if x>len(s[i]): print(0); return
        if len(ans)==1 or len(out)==1:
            if ans[0]==-1 and ans[0]==out[0] : 
                continue
            else: print(0); return
        sl1,sl2,sl3=0,0,0
        for k in range(ans[0]-1,ans[1]):
            if s[i][k]=='1': sl1+=1
        for k in range(ans[2]-1,ans[3]):
            if s[i][k]=='1': sl2+=1
        for k in range(out[2]-1,out[3]):
            if s[i][k]=='1': sl3+=1
        if sl1!=sl2 or sl2!=sl3 or sl1!=sl3: print(0); exit(0)
    print(1)
try:
    solve()
except Exception as e:
    f= open(os.path.join(cwd,"err.or"),"w",encoding="utf-8")
    f.write(str(e))
    f.close()

    
