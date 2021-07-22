import serverutils
import os

repository_root = os.environ[serverutils.get_repository_root()]
server_root = os.path.join(repository_root, 'servers')
    
for root, dirnames, filenames in os.walk(server_root):
    for filename in filenames:
        if filename is not 'file_cleanser.py' and filename is not 'serverutils.py': 
            file_n, file_e = os.path.splitext(filename)
            if file_e == '.py':
                path = os.path.join(root, filename)
                f = open(path, 'r')
                for line in f.readlines():
                    if filename != 'file_cleanser.py' and filename != 'serverutils.py':
                        if 'os.environ[' in line:
                            print(('\n' + path))
                            print(line.strip())
                            
                            
### lets move this and server utils out of the main servers directory -> where should they live?