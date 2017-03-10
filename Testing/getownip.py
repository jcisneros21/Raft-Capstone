import subprocess
import re

result = subprocess.check_output(['ifconfig'], universal_newlines=True)
ips = re.findall('inet addr:[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', result)

for i in range(len(ips)):
    if ips[i][10:12] == '10':
        print(ips[i][10:])

