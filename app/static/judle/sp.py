import subprocess
import os
data, temp = os.pipe()
# write to STDIN as a byte object(convert string
# to bytes with encoding utf8)
os.write(temp, bytes("5\n10", "utf-8"))
os.close(temp)
s = subprocess.check_output("scratch-run ab.sb3", stdin=data, shell=True)
print(s.decode("utf-8"))
