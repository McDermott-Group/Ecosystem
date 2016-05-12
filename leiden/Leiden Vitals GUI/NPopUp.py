
from PyQt4 import QtCore, QtGui
class PopUp(QtGui.QDialog):
	'''Small class for a popup window'''
	consent = None
	def __init__(self, message, parent=None):
		'''Initialize the pop-up'''
		# The user gives a message to display.
		self.msg = message
		# Initialize the rest of the widget.
		QtGui.QWidget.__init__(self, parent)
		#self.ui = Ui_Dialog()
		self.setupUi(self)
		
	def setupUi(self, Dialog):
		'''Configure the look and function of the pop up'''
		self.setObjectName("Warning")
		self.resize(500,400)
		self.setStyleSheet("background:rgb(70, 80, 88)")
		
		frame = QtGui.QFrame(self)
		frame.setGeometry(QtCore.QRect(10,10, 480, 300))
		frame.setStyleSheet("background: rgb(52, 73, 94)")
		frame.setFrameShape(QtGui.QFrame.WinPanel)
		frame.setFrameShadow(QtGui.QFrame.Plain)
		frame.setLineWidth(2)
		# Create a new label that will display the message.
		self.warning = QtGui.QLabel(frame)
		self.warning.setText(self.msg)
		frameHBox = QtGui.QHBoxLayout()
		frame.setLayout(frameHBox)
		frameHBox.addWidget(self.warning)
		mainHBox = QtGui.QHBoxLayout()
	
		# Configure a font to use.
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setBold(False)
		font.setWeight(50)
		font.setKerning(True)
		# Apply the formatting to the message.
		self.warning.setWordWrap(True)
		self.warning.setAlignment(QtCore.Qt.AlignCenter)
		self.warning.setStyleSheet("color:rgb(189, 195, 199);")
		self.warning.setFont(font)
		# Create an 'Ok' button at the bottom of the screen.
		self.okButton = QtGui.QPushButton(Dialog)
		self.okButton.setStyleSheet("color:rgb(189, 195, 199); background: rgb(52, 73, 94)")
		self.okButton.setGeometry(QtCore.QRect(20, 330, 191, 61))
		self.okButton.setText("Ok")
		#self.okButton.setStyleSheet("background-color: green")
		self.okButton.setFont(font)
		self.okButton.clicked.connect(self.okClicked)
		# Create a 'Cancel button' at the bottom of the screen.
		self.cancelButton = QtGui.QPushButton(Dialog)
		self.cancelButton.setStyleSheet("color:rgb(189, 195, 199); background: rgb(52, 73, 94)\n")
		self.cancelButton.setGeometry(QtCore.QRect(290, 330, 191, 61))
		self.cancelButton.setText("Cancel")
		#self.cancelButton.setStyleSheet("background-color: maroon")
		self.cancelButton.setFont(font)
		self.cancelButton.clicked.connect(self.cancelClicked)
		
	def okClicked(self):
		'''Called when the ok button is clicked'''
		# Clicking the ok button gives consent for whatever you are doing.
		self.consent = True
		# Close the popup
		self.close()
	def cancelClicked(self):
		'''Called when the cancel button is clicked.'''
		# The user has not given consent.
		self.consent = False
		# Close the popup.
		self.close()