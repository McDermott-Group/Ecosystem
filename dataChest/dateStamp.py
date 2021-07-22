# Copyright (C) 2016  Alexander Opremcak
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import date, datetime, timedelta
from dateutil import tz
import re

class dateStamp(object):
    
  def _intToAlphabet(self, num):
      base = 26
      if num > 0:
          digits = []
          while num:
              digits.append(int(num % base))
              num /= base
          converted_digits = digits[::-1]
      elif num == 0:
          converted_digits = [0]
      elif num <0:
          print("no negative numbers!!!")
      letters = list("abcdefghijklmnopqrstuvwxyz")
      for ii in range(0, len(converted_digits)):
          converted_digits[ii] = letters[converted_digits[ii]]
      converted_digits = "".join(converted_digits)
      for jj in range(len(converted_digits),3):
          converted_digits = 'a' + converted_digits
      return converted_digits

  def _base26ToInt(self, chars):
      chars = list(chars)
      letters = list("abcdefghijklmnopqrstuvwxyz")
      for ii in range(0, len(chars)):
          for jj in range(0, len(letters)):
              if chars[ii] == letters[jj]:
                  chars[ii] = jj
      result = 0
      for kk in range(0, len(chars)):
          result = result + (26**kk)*int(chars[len(chars)-kk-1])
      return result

  def _intToYYYYMMDD(self, num):
      t0 = datetime(2015, 1, 1)
      tNow = str(t0 + timedelta(days=num))
      return tNow.split()[0]

  def _intToSeconds(self, num):
      dt = 60.0/(26**3-1)
      return dt*num
            
  def dateStamp(self, utcDateIso = None):
      """Change ``num'' to given base
      Upto base 36 is supported."""
      if utcDateIso == None:
          utcDateIso = datetime.utcnow().isoformat()
      ymd = utcDateIso.split("T")[0].split("-")
      hms = utcDateIso.split("T")[1].split(":")
      hour = hms[0]
      minute = hms[1]
      secs = hms[2]
      dt = 60.0/(26**3-1)
      t = int(round(float(secs)/dt)) ## do this cleverly
      d0 = date(2015, 1, 1)
      d1 = date(int(ymd[0]), int(ymd[1]), int(ymd[2]))
      delta = d1 - d0
      numDays = delta.days
      ymdConverted = self._intToAlphabet(numDays)
      secsConverted = self._intToAlphabet(t)
      return ymdConverted+hour+minute+secsConverted

  def utcDateIsoString(self):
    utcDateISO = datetime.utcnow().isoformat()
    return utcDateISO

  def localDateIsoString(self):
    dateISO = datetime.now().isoformat()
    return dateISO
    

  def invertDateStamp(self, dateStamp):
      ymd = dateStamp[0:3]
      secs = dateStamp[7:10]
      ymd = self._base26ToInt(ymd)
      ymd = self._intToYYYYMMDD(ymd)
      secs = self._base26ToInt(secs)
      secs = self._intToSeconds(secs)
      secs = '{:09.6f}'.format(secs)
      return ymd +'T'+dateStamp[3:5]+':'+dateStamp[5:7]+':'+secs

  def floatToUtcDateStr(self, utcFloat):
    if isinstance(utcFloat, float):
      dateStr = datetime.utcfromtimestamp(utcFloat).isoformat()
      if len(dateStr) == 19:
        dateStr = dateStr + ".000000"
      return dateStr
    else:
      raise IOError("Inputs can only be of type float.")
    
  def utcNowFloat(self):
    utcNow = datetime.utcnow()
    timeZero = datetime(1970,1,1)
    return (utcNow-timeZero).total_seconds()

  def localDateStrToFloat(self, localDateStr):
    if self._isStringDateISOFormat(localDateStr):
      localDatetime = datetime.strptime(localDateStr,'%Y-%m-%dT%H:%M:%S.%f')
      utc = tz.tzutc()
      local = tz.tzlocal()
      declareTzoneToLocal = localDatetime.replace(tzinfo = local)
      convertToUTC = declareTzoneToLocal.astimezone(utc).isoformat()
      print("convertToUTC=", convertToUTC[:-5])
      return self.utcDateStrToFloat(convertToUTC[:-6])
    else:
      raise IOError("Input strings should be Date ISO formatted.")

  def utcDateStrToFloat(self, utcDateStr):
    if self._isStringDateISOFormat(utcDateStr):
      utcDatetime = datetime.strptime(utcDateStr,'%Y-%m-%dT%H:%M:%S.%f')
      timeZero = datetime(1970,1,1)
      return (utcDatetime-timeZero).total_seconds()
    else:
      raise IOError("Input strings should be Date ISO formatted.")

  def _isStringDateISOFormat(self, dateStr): #checks for regular expression
    RE = re.compile(r'^\d{4}-\d{2}-\d{2}[T]\d{2}:\d{2}:\d{2}[.]\d{6}$')
    return bool(RE.search(dateStr))

      
    
      
