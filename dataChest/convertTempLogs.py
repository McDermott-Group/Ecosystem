from dataChest import dataChest
from dateStamp import dateStamp
import datetime
#import timezone as tz
from dateutil import tz
import glob
import os
import struct

tempDataChest = dataChest(['ADR Logs','ADR3'])
#tempDataChest.cd(['ADR3'])

# file_path = base_path + '\\temperatures' + date_append + '.temps'
filesToConvert = glob.glob('/afs/physics.wisc.edu/mcdermott-group/Data/ADR_log_files/ADR3/*.temps')
#filesToConvert = filesToConvert[0:1]
for file_path in filesToConvert:
    file_length = os.stat(file_path)[6]
    timeString = file_path.split('temperatures')[-1]
    print 'converting %s'%timeString
    localTime = datetime.datetime.strptime(timeString, '_%y%m%d_%H%M.temps')
    localTime = localTime.replace(tzinfo=tz.tzlocal())
    utc = localTime.astimezone(tz.tzutc())
    dts = dateStamp()
    iso = utc.isoformat().split('+')[0] # dateStamp doesn't deal properly with iso with TZ info
    dtstamp = dts.dateStamp(iso)

    tempDataChest.createDataset("temperatures",
                    [('time',[1],'utc_datetime','')],
                    [('temp60K',[1],'float64','Kelvin'),('temp03K',[1],'float64','Kelvin'),
                     ('tempGGG',[1],'float64','Kelvin'),('tempFAA',[1],'float64','Kelvin')],
                     dateStamp=dtstamp)
    tempDataChest.addParameter("X Label", "Time")
    tempDataChest.addParameter("Y Label", "Temperature")
    tempDataChest.addParameter("Plot Title", utc.strftime("ADR temperature history for run starting on %y/%m/%d %H:%M"))

    try:
        with open(file_path, 'rb') as f:
            n = 1
            while file_length - n*5*8 > 0:
                f.seek(n*5*8)
                newRow = [struct.unpack('d',f.read(8))[0] for x in ['time','t1','t2','t3','t4']]
                utc = datetime.datetime.utcfromtimestamp(newRow[0]) # for float
                utc = utc.replace(tzinfo=tz.tzlocal()) # local
                utc = utc.astimezone(tz.tzutc()) # utc
                epoch = datetime.datetime(1970, 1, 1).replace(tzinfo=tz.tzutc())
                newRow[0] = (utc - epoch).total_seconds()
                tempDataChest.addData([newRow])
                n += 1
    except IOError: print '%s could not be converted.'%file_path
