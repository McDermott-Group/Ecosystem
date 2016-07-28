start /b C:\Users\McDermott_Clean_Room\Documents\McDermott\Area51\scalabrad\bin\labrad.bat
timeout 4
start /b python C:\Users\McDermott_Clean_Room\Documents\McDermott\Servers\buses\serial_server.py
timeout 2
start /b python C:\Users\McDermott_Clean_Room\Documents\McDermott\Servers\instruments\serialdevices\LaserEndpointMonitor.py
timeout 2
start /b python C:\Users\McDermott_Clean_Room\Documents\McDermott\Servers\telecommServer.py
timeout 2
start /b python C:\Users\McDermott_Clean_Room\Documents\McDermott\Servers\GUI\LaserEndpoint\LaserEndpointGui.py
timeout 2
exit
