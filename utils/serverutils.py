from os         import environ, path, walk
from fnmatch    import filter

def get_data_root():
    return 'DATA_ROOT'
    
def get_repository_root():
    return 'REPOSITORY_ROOT'
    
def locate(target, root_path = None):
    """ 
    Locate a file in repositories or any subfolder thereof
    
    target: the name of the file to be located, can be specified
            with or without an extension.
            
    root_path: absolute path within of subdirectory to be searched. 
               
    returns: the absolute path of the target as a string.
    """
    
    t_name, t_extension = path.splitext(target)
    found = False
    extensionless = (t_extension == '')
    repository_root = environ[get_repository_root()]
    
    if root_path is None:
        root_path = path.join(repository_root, 'servers')

    for root, dirnames, filenames in walk(root_path):
        if extensionless:
            for filename in filenames:
                f, e = path.splitext(filename)
                if f == target:
                    if found:
                        raise LookupError('Multiple files in ' + root_path + ' match ' + target + '... try specifying an extension.')
                        return None
                    
                    destination = path.join(root, filename)
                    found = True
        
        else:
            for filename in filter(filenames, target):
                destination = path.join(root, filename)
                if found:
                    raise LookupError('Multiple files in ' + root_path + ' match ' + target + '... resolve this conflict.')
                    return None
                    
                found = True
    
    if found: 
        return destination
    else: 
        raise LookupError('Could not find file: ' + target + ' in ' + root_path)
