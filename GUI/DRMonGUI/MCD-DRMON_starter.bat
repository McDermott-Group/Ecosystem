start /b C:\Users\McDermott\Documents\McDermott-group\Area51\scalabrad\bin\labrad.bat
timeout 2
start /b python C:\Users\McDermott\Documents\McDermott-group\Servers\buses\gpib_server.py
timeout 2
start /b python C:\Users\McDermott\Documents\McDermott-group\Servers\buses\gpib_device_manager.py
timeout 2
start /b python C:\Users\McDermott\Documents\McDermott-group\Servers\buses\serial_server.py
timeout 2
start /b python C:\Users\McDermott\Documents\McDermott-group\Servers\instruments\gpibdevices\lakeshore218.py
timeout 2
start /b python C:\Users\McDermott\Documents\McDermott-group\Servers\instruments\serialdevices\MKSPDR2000.py
timeout 2
start /b python C:\Users\McDermott\Documents\McDermott-group\Servers\telecommServer.py
timeout 2
start /b python C:\Users\McDermott\Documents\McDermott-group\Servers\GUI\DRMonGUI\DRMonGUI.py

exit