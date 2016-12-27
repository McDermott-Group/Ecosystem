start /b C:\Users\Student\Desktop\GitRepositories\Area51\scalabrad\bin\labrad.bat
timeout 8
start /b C:\Users\Student\Desktop\GitRepositories\Servers\buses\serial_server.py
timeout 5
start /b C:\Users\Student\Desktop\GitRepositories\Servers\instruments\serialdevices\cryomech_cp2800_compressor.py
timeout 1
start /b C:\Users\Student\Desktop\GitRepositories\Servers\instruments\serialdevices\omega_ratemeter.py
timeout 1
start /b C:\Users\Student\Desktop\GitRepositories\Servers\instruments\serialdevices\omega_temperature_monitor.py
timeout 1
start /b C:\Users\Student\Desktop\GitRepositories\Servers\instruments\serialdevices\pfeiffer_vacuum_maxigauge.py
timeout 1
start C:\Users\Student\Desktop\GitRepositories\Servers\instruments\serialdevices\LeidenPT1000\LeidenPT1000.py
timeout 1
start /b C:\Users\Student\Desktop\GitRepositories\Servers\instruments\leiden_dr_temperature.py
timeout 1
start /b python C:\Users\Student\Desktop\GitRepositories\Servers\telecommServer.py
timeout 5
start python C:\Users\Student\Desktop\GitRepositories\Servers\GUI\LeidenVitalsGUI\LeidenGui.py

exit