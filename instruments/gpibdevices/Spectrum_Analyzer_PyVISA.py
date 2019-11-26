import pyvisa
import time
import numpy as np

rm = pyvisa.ResourceManager()
sa = rm.open_resource('GPIB0::16::INSTR')
sa.encoding = "latin-1"

# d0 = sa.query('TDF B; TRB?;')
# print(type(d0))

# d = map(ord, sa.query('TDF B; TRA?;'))
# d_new = np.zeros(401)
# print(d_new)
# for i in range(401):
#     d_new[i] = d[2*i]*1000+d[2*i+1]
#
# d_new_scale = 80*d_new/30000-80
# print(d_new_scale)


"""Below is a working example"""
# rm = pyvisa.ResourceManager()
# sa = rm.open_resource('GPIB0::16::INSTR')
# sa.encoding = "latin-1"
# for i in range(1):
#     print('i=', i)
#     t1 = time.time()
#     print(map(ord, sa.query('TDF B; TRA?;')))
#     t2 = time.time()
#     print('t_d=', t2-t1)
