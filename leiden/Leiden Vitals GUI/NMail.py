# Copyright (C) 2016 Noah Meltzer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Utilities libraries.


"""
# version = 1.0.1
# description = Very simple email client.
"""

import smtplib
from email.mime.text import MIMEText

class NMail:
	def __init__(self, To, From, Subject, Body):
		msg = MIMEText(Body)
		print("Mailing")
		msg['Subject'] =  Subject
		msg['From'] = From
		msg['To'] = To
		# We use gmail
		smtpObj = smtplib.SMTP('smtp.gmail.com')
		# Say hello to gmail servers
		smtpObj.ehlo()
		# Initialize TLS security
		smtpObj.starttls()
		# try:
			# Login
		#print(msg.as_string())
		if(len(To) is not 0):
			print To
			smtpObj.login('physics.labrad@gmail.com', 'mcdermott')
			# Send the mail
			print("To")
			smtpObj.sendmail('physics.labrad@gmail.com',To.split(',') , msg.as_string())         
			print "Successfully sent mail"
		smtpObj.quit()
		# except:
			# print "Mail failed."
# except:
	# print "Error: unable to send email"
