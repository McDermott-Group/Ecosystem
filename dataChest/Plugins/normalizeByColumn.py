#TITLE: Normalize By Column
#DESCR: Fits plot to blah blah blah

def run(data):
    print 'SIZE ',data.shape
    return data/data.max(0)
