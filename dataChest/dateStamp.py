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

class dateStamp:
    
  def intToAlphabet(self, num):
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
          print "no negative numbers!!!"
      letters = list("abcdefghijklmnopqrstuvwxyz")
      for ii in range(0, len(converted_digits)):
          converted_digits[ii] = letters[converted_digits[ii]]
      converted_digits = "".join(converted_digits)
      for jj in range(len(converted_digits),3):
          converted_digits = 'a' + converted_digits
      return converted_digits

  def base26ToInt(self, chars):
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

  def intToYYYYMMDD(self, num):
      t0 = datetime(2015, 1, 1)
      tNow = str(t0 + timedelta(days=num))
      return tNow.split()[0]

  def intToSeconds(self, num):
      dt = 60.0/(26**3-1)
      return dt*num
            
  def dateStamp(self, dateISO = None):
      """Change ``num'' to given base
      Upto base 36 is supported."""
      if dateISO == None:
          dateISO = datetime.now().isoformat()
      #print dateISO
      ymd = dateISO.split("T")[0].split("-")
      hms = dateISO.split("T")[1].split(":")
      hour = hms[0]
      minute = hms[1]
      secs = hms[2]
      dt = 60.0/(26**3-1)
      t = int(round(float(secs)/dt)) ## do this cleverly
      d0 = date(2015, 1, 1)
      d1 = date(int(ymd[0]), int(ymd[1]), int(ymd[2]))
      delta = d1 - d0
      numDays = delta.days
      ymdConverted = self.intToAlphabet(numDays)
      secsConverted = self.intToAlphabet(t)
      return ymdConverted+hour+minute+secsConverted

  def invertDateStamp(self, dateStamp):
      ymd = dateStamp[0:3]
      secs = dateStamp[7:10]
      ymd = self.base26ToInt(ymd)
      ymd = self.intToYYYYMMDD(ymd)
      secs = self.base26ToInt(secs)
      secs = self.intToSeconds(secs)
      secs = str(secs)
      if len(secs.split(".")[0])==1:
          secs = '0'+secs
      return ymd +'T'+dateStamp[3:5]+':'+dateStamp[5:7]+':'+secs 
