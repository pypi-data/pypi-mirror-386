import sys
import subprocess

def cmd(cmd,prt=1):
    if type(cmd)==str:
        cmd = cmd.split(" ")
    try:
        if prt: print(" ".join(cmd),end="\n\n")
        result = subprocess.run(
            cmd,  # Command that will generate an error
            capture_output=True,         # Capture both stdout and stderr
            text=True,                   # Decode output as text (UTF-8 by default)
            check=True,                   # Raise CalledProcessError if return code is non-zero
            shell=True
        )
        if prt: print("STDOUT:", result.stdout)
        if result.stderr:
            if prt: print("STDERR:", result.stderr)
        else:
            if prt: print("STDERR: EMPTY")
        if prt: print("\n")
    except subprocess.CalledProcessError as e:
        if prt: print("Error occurred:")
        if prt: print("STDOUT:", e.stdout)
        if prt: print("STDERR:", e.stderr)

if __name__=="__main__":
    try:
        cmd(sys.argv[1])
    except:
        cmd("dir")
