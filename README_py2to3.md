# Notes on transition

 * Changes in code are commented '# python 2to3'
 * Upgraded grapher to pyQt5

# Instructions to transition a workspace from python 2 to python 3

 1. Install python 3.7 (No higher, yet)
 2. Create folder: 'C:\Repositories3'
 3. Create subfolders: 'C:\Repositories3\Analysis', 'C:\Repositories3\area51', 'C:\Repositories3\measurement', 'C:\Repositories\servers', 'C:\Repositories3\Simulation-and-Design'
 4. Clone those four repositories. Make sure to pull from the python3 branch.
 5. Update environment variable: REPOSITORY_ROOT: 'C:\Repositories3'
 6. Update environment variable: PYTHONPATH: 'C:\Repositories3\servers\dataChest', 'C:\Repositories3\servers\utils', 'C:\Repositories3\measurement\general\database'
 7. Install python packages (see below for details)

# Python packages by file

dataChest.py:
 * python3 -m pip install h5py
 * python3 -m pip install python-dateutil

grapher_pyQt5.py:
 * python3 -m pip install pyqt5
 * python3 -m pip install pyqtgraph


