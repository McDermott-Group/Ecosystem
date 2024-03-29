import labrad

cxn = labrad.connect()

adr = cxn.adr3

adr.set_pid_kp(0.75)
adr.set_pid_ki(0)
adr.set_pid_kd(15)
