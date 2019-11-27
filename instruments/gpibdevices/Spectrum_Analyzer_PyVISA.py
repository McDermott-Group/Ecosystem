import pyvisa
import struct
import time
import numpy as np

rm = pyvisa.ResourceManager()
sa = rm.open_resource('GPIB0::16::INSTR')

# dp = sa.query('TDF P; TRA?;')
# print(dp)

# t1 = time.time()
# dm = sa.query('TDF M; TRA?;')
# dm_dBm = np.zeros(401)
# t2 = time.time()
# print(t2-t1)
# print(dm)

#
sa.encoding = "latin-1"
for i in range(10):
    print('i=', i)
    t1 = time.time()
    sa.write('TDF B; TRA?;')
    d = sa.read_raw()
    # d = sa.query('TDF B; TRA?;')
    d_m = np.asarray(struct.unpack('>401H', d))
    d_m_dBm = np.zeros(401)
    for i in range(401):
        d_m_dBm[i]=d_m[i]/100.0-80.0
    # print(d_m_dBm)
    t2 = time.time()
    print(t2-t1)


# """Below is a working example for binary data"""
# rm = pyvisa.ResourceManager()
# sa = rm.open_resource('GPIB0::16::INSTR')
# Real value
# dp = sa.query('TDF P; TRA?;')
# print(dp)
# Binary
# sa.encoding = "latin-1"
# for i in range(1):
#     print('i=', i)
#     t1 = time.time()
#     data = sa.query('TDF B; TRA?;')
#     print(map(ord, sa.query('TDF B; TRA?;')))
#     # print(map(ord, sa.query('TDF B; TRA?;')))
#     t2 = time.time()
#     print('t_d=', t2-t1)
