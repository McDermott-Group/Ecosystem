:: Start labrad server; Web server; telecommServer; serialServer;
:: Lakshore211Server and the GUI
SET REPO=C:\Repositories
START /b %REPO%\area51\scalabrad\bin\labrad.bat
timeout 2
START /b %REPO%\area51\scalabrad-web-server\bin\labrad-web.bat
timeout 2
START /b python %REPO%\servers\telecommServer.py
timeout 2
START /b python %REPO%\servers\buses\serial_server.py
timeout 2
START /b python %REPO%\servers\instruments\serialdevices\lakeshore_211_Server.py
timeout 2
START /b python %REPO%\servers\GUI\Lakeshore211GUI\lk211View.py
timeout 2
EXIT
