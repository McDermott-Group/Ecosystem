import smtplib
import NMail
import threading
import time
#from email.mime.text import MIMEText

class NAlert:
	def __init__(self,mins, maxs, contacts,  devices):
		#print "Mins: ", mins, " \r\nMaxs:", maxs, " \r\nContacts:", contacts
		
		self.devices = devices
		self.mins = mins
		self.maxs = maxs
		self.contacts = contacts
		self.message = []
		self.t1 = 0
		self.mailSent =[]
		
		self.keepGoing = True
		
		for i in range(0, len(self.devices)):
			for y in range(0, len(self.devices[i].getFrame().getNicknames())):
				self.mailSent.append(False)
				
		
		self.deviceThread = threading.Thread(target = self.monitorReadings, args=[])
		# If the main thread stops, stop the child thread
		self.deviceThread.daemon = True
		# Start the thread
		self.deviceThread.start()
	
	def monitorReadings(self):
		z = 0
		for i in range(0, len(self.devices)):
			if(self.devices[i].getFrame().getReadings() is not None):
				for y in range(0, len(self.devices[i].getFrame().getReadings())):
					if(self.devices[i].getFrame().getNicknames()[y] is not None):
						
						if(self.mins[z]>self.devices[i].getFrame().getReadings()[y]):
							if(self.mins[z] is not ''):
								#print(self.mins[z])
								self.generateMessage(z,y,i)
								#print(z)
								self.sendMail(i, y, z)
								#print(self.mins[z])
							
						if(self.maxs[z]<self.devices[i].getFrame().getReadings()[y]):
							if(self.maxs[z] is not ''):
								self.generateMessage(z,y,i)
								self.sendMail(i, y, z)
						z = z+1
		if(self.keepGoing):
			threading.Timer(1, self.monitorReadings).start()
			
	def stop(self):
		self.keepGoing = False
	def generateMessage(self,z, y, i):
		#print "HERE 1 ", z
		try:
			if(not self.mailSent[z]):
				#print("try")
				self.message.append(("On "
					+time.asctime( time.localtime(time.time()) )
					+", the "+self.devices[i].getFrame().getTitle()+"'s "
					+ self.devices[i].getFrame().getNicknames()[y] + " was "+
					str(self.devices[i].getFrame().getReadings()[y])+
					self.devices[i].getFrame().getUnits()[y] +
					" which is out of the specified range of "
					+str(self.mins[z]) 
					+ self.devices[i].getFrame().getUnits()[y]+
					" - " +str(self.maxs[z])+
					self.devices[i].getFrame().getUnits()[y]+"."))
				
				self.mailSent[z] = True
				
		except:
			#print("except")
			self.mailSent.append(False)
			
			#print(self.mins)
			#print(self.mins[z])
		#print "HERE 2 ",z
		#print self.message
			
	def sendMail(self, i, y, z):
		HOURS_BETWEEN_EMAILS = 0.003
		elapsedHrs = (time.time()-self.t1)/3600
		
		
		if(HOURS_BETWEEN_EMAILS<elapsedHrs):
			NMail.NMail(self.contacts[z],self.devices[i].getFrame()
				.getTitle(), self.devices[i].getFrame().getNicknames()[y], str(self.message))
			print(self.message)
			self.message = []
			self.mailSent = []
			
			self.t1 = time.time()
	