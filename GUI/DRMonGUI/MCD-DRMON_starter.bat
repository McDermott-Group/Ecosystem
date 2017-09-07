start /b C:\Repositories\area51\scalabrad\bin\labrad.bat
timeout 2
start /b C:\Repositories\area51\scalabrad-web-server\bin\labrad-web.bat
timeout 2
start /b python C:\Repositories\servers\buses\gpib_server.py
timeout 2
start /b python C:\Repositories\servers\buses\gpib_device_manager.py
timeout 2
start /b python C:\Repositories\servers\buses\serial_server.py
timeout 2
start /b python C:\Repositories\servers\instruments\gpibdevices\lakeshore218.py
timeout 2
start /b python C:\Repositories\servers\instruments\gpibdevices\lakeshore370_simple.py
timeout 2
start /b python C:\Repositories\servers\instruments\serialdevices\mks_pdr2000.py
timeout 2
start /b python C:\Repositories\servers\telecommServer.py
timeout 2
start /b python C:\Repositories\servers\GUI\DRMonGUI\DRMonGUI.py

exit