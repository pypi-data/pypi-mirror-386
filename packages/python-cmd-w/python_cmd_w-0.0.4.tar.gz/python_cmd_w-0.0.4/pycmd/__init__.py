import sys
import subprocess
import chardet

def cmd(command,prt=1):
    if prt: print(command)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    p.wait()
    r = {"process":p,"output":0,"error":0}
    try:
        o = p.stdout.read()
        ec = chardet.detect(o)["encoding"]
        o = o.decode(ec)
        p.stdout.close()
        r["output"] = o
        if prt: print("output",o)
    except AttributeError :
        if prt: print("output empty")
    try:
        e = p.stderr.read()
        ec = chardet.detect(e)["encoding"]
        e = e.decode(ec)
        p.stderr.close()
        if prt: print("error",o)
        r["error"] = e
    except AttributeError :
        if prt: print("error empty")
    return r

if __name__=="__main__":
    try:
        cmd(sys.argv[1])
    except:
        cmd("dir")
