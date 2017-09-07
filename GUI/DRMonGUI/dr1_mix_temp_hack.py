import labrad
import os
import time


LOGPATH = os.path.join("Z:","mcdermott-group","data","fridgeLogs","dr1","current_mix_temp.dat")


REFRESH_INTERVAL = 30

cxn = labrad.connect()

RuOx = cxn.lakeshore_ruox
RuOx.select_device()


while True:
    current_temps = RuOx.temperatures()
    mean_temp = (current_temps[0]+current_temps[1])/2.0
    with open(LOGPATH, 'w') as f:
        f.write("{:f}".format(mean_temp))
        print('File updated.')
    time.sleep(REFRESH_INTERVAL)