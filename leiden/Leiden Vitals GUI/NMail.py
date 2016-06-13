import smtplib
from email.mime.text import MIMEText
#fp = open(textfile, 'rb')
# Create a text/plain message
class NMail:
	def __init__(self, To, From, Subject, Body):
		msg = MIMEText(Body)
		#fp.close()

		msg['Subject'] =  Subject
		msg['From'] = From
		msg['To'] = To

		# try:

		smtpObj = smtplib.SMTP('smtp.gmail.com')
		smtpObj.ehlo()
		smtpObj.starttls()
		try:
			smtpObj.login('physics.labrad@gmail.com', 'mcdermott')

			smtpObj.sendmail('physics.labrad@gmail.com',To , msg.as_string())         
			print "Successfully sent mail"
			smtpObj.quit()
		except:
			print "Mail failed."
# except:
	# print "Error: unable to send email"