import smtplib
import MMail
import threading
import time
import sys
sys.dont_write_bytecode = True
#from email.mime.text import MIMEText

class MAlert:
	def __init__(self,checkBoxes,mins, maxs, contacts,  devices, tele):
		# Configure all public variables
		self.devices = devices
		self.mins = mins
		self.maxs = maxs
		self.contacts = contacts
		self.message = []
		self.checkBoxes = checkBoxes
		self.tele = tele
		self.t1 = 0
		# Have the specified people been notified about the specific device?
		self.mailSent =[]
		# Keep running, this is false when settings are changed and a 
		# new NAlert instance is created. Setting this to false terminates
		# the thread.
		self.keepGoing = True
		# Keep track of which mail was sent
		for i in range(0, len(self.devices)):
			for y in range(0, len(self.devices[i].getFrame().getNicknames())):
				if(self.devices[i].getFrame().getNicknames()[y] is not None):
					self.mailSent.append(False)
					#print(len(self.mailSent))
	def begin(self):
		# This runs on its own thread
		self.deviceThread = threading.Thread(target = self.monitorReadings, args=[])
		# If the main thread stops, stop the child thread
		self.deviceThread.daemon = True
		# Start the thread
		self.deviceThread.start()
	
	def monitorReadings(self):
		'''Monitor the readings for issues'''
		# Z keeps track of which index we are on for arrays which are not 2D.
		z = 0
		# For all devices
		for i in range(0, len(self.devices)):
			# If it has readings
			if(self.devices[i].getFrame().getReadings() is not None):
				# Loop through all readings
				for y in range(0, len(self.devices[i].getFrame().getNicknames())):
					# If the reading is displayed on the GUI
					#print(self.devices[i].getFrame().getNicknames())
					if(self.devices[i].getFrame().getNicknames()[y] is not None):
						# Get that specific reading
						#print self.mins
						if len(self.mins) is not 0:
							if(len(str(self.mins[z])) is not 0):
								if(float(self.mins[z])>float(self.devices[i].getFrame().getReadings()[y])):
								# If a min has been specified
									if(self.checkBoxes[z]):
									#print "mins", (self.mins)
										self.generateMessage(z,y,i)
										self.sendMail(i, y, z)
									#print(self.mins[z])
						if len(self.maxs) is not 0:
							if(len(str(self.maxs[z])) is not 0):
								if(float(self.maxs[z])<float(self.devices[i].getFrame().getReadings()[y])):
									if(self.checkBoxes[z]):
										self.generateMessage(z,y,i)
										self.sendMail(i, y, z)
						z = z+1
			else:
				
				z=z+len(self.devices[i].getFrame().getNicknames())
		if(self.keepGoing):
			threading.Timer(1, self.monitorReadings).start()
			
	def stop(self):
		self.keepGoing = False
		
	def generateMessage(self,z, y, i):
		if(not self.mailSent[z]):
			self.message.append(("Time: "
				+time.asctime( time.localtime(time.time()) )
				+" | "+self.devices[i].getFrame().getTitle()+"->"
				+ self.devices[i].getFrame().getNicknames()[y] + ": "+
				str(self.devices[i].getFrame().getReadings()[y])+
				self.devices[i].getFrame().getUnits()[y] +
				" | Range: "
				+str(self.mins[z]) 
				+ self.devices[i].getFrame().getUnits()[y]+
				" - " +str(self.maxs[z])+
				self.devices[i].getFrame().getUnits()[y]+"."))
			
			self.mailSent[z] = True
	def sendMail(self, i, y, z):
		'''Send mail if the given amount of time has elapsed.'''
		HOURS_BETWEEN_EMAILS = 0.0003
		elapsedHrs = (time.time()-self.t1)/3600
		
		
		if(HOURS_BETWEEN_EMAILS<elapsedHrs):
			success, address = self.tele.send_sms(self.devices[i].getFrame().getNicknames()[y], 
									str(self.message), 
									self.contacts[z].split(','),
									"labrad_physics")
			if (not success):
				print("Couldn't send email to group: "+str(self.contacts[z].split(','))+ 
				", someone may be missing from the registry or incorrectly entered.")
			self.message = []
			self.mailSent = []
			for i in range(0, len(self.devices)):
				for y in range(0, len(self.devices[i].getFrame().getNicknames())):
					if(self.devices[i].getFrame().getNicknames()[y] is not None):
						self.mailSent.append(False)
			self.t1 = time.time()
	
