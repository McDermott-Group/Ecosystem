start /b C:\Users\Noah\OneDrive\mcDermott\Area51\scalabrad\bin\labrad.bat
timeout 5
start /b python C:\Users\Noah\OneDrive\mcDermott\Servers\telecommServer.py
timeout 2
start /b python C:\Users\Noah\OneDrive\mcDermott\Servers\GUI\TestGui\dummyServer.py
timeoout 2
start /b python C:\Users\Noah\OneDrive\mcDermott\Servers\GUI\TestGui\dummyServer2.py
timeoout 2

start /b python C:\Users\Noah\OneDrive\mcDermott\Servers\GUI\TestGui\testGui.py

exit