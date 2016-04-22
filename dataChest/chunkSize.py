from dataChest import dataChest
from dateStamp import dateStamp
import datetime
from dateutil import tz
import glob
import os
import struct

tempDataChest = dataChest(['ADR Logs','Chunk Size'])
tempDataChest.createDataset("fileSize",
                [('index',[1],'int64','')],
                [('fileSize',[1],'int64','bytes')])
tempDataChest.addParameter("X Label", "index")
tempDataChest.addParameter("Y Label", "file size")
tempDataChest.addParameter("Plot Title", 'file size')

# file_path = base_path + '\\temperatures' + date_append + '.temps'
filesToConvert = glob.glob('/afs/physics.wisc.edu/mcdermott-group/Data/ADR_log_files/ADR3/*.temps')

i=0
#filesToConvert = filesToConvert[0:1]
for file_path in filesToConvert:
    file_length = os.stat(file_path)[6]
    i += 1
    tempDataChest.addData([[i,file_length]])
