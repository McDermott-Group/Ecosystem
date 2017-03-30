# Copyright (C) 2016 Noah Meltzer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

__author__ = "Noah Meltzer"
__copyright__ = "Copyright 2016, McDermott Group"
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Noah Meltzer"
__status__ = "Beta"

import cPickle as pickle
import traceback 
import os


class MPersistentData:

    persistentDataDict = {}
    def __init__(self):
        #print "Loading persistent data..."
        self.location = os.path.dirname(traceback.extract_stack()[0][0])
        self.name = 'mview.config'
        try:
            self.restoreState()
        except:
            print "The mview.config file was not found."


    def saveState(self):
        #print self.persistentDataDict
        print "Pickling and saving data to file..."
        #print self.persistentDataDict
        pickle.dump(self.persistentDataDict, open(os.path.join(self.location, self.name), 'wb'))
        print "data pickled and saved."
    def restoreState(self):
        
        self.persistentDataDict = pickle.load(open(os.path.join(self.location, self.name), 'rb'))
        #print self.persistentDataDict
    def persistentDataAccess(self, val, *args, **kwargs):
        #print "h1"
        #traceback.print_exc()
        default = kwargs.get("default", None)
        currentLevel = self.persistentDataDict
        previousLevel = currentLevel
        previousekey = args[0]
        for i,key in enumerate(args):
             
            if type(currentLevel) is dict:
                previousLevel = currentLevel
                previouskey = key
            
            else:
                previousLevel[previouskey] = {}
            if key in currentLevel.keys():
                currentLevel = currentLevel[key]
            else:
                currentLevel[key] = {}
                currentLevel = currentLevel[key]
        #print cls.persistentDataDict
        if val != None:
            previousLevel[previouskey] = val
        else:
            if previousLevel[previouskey] == {}:
                previousLevel[previouskey] = default
            #print self.persistentDataDict
            return previousLevel[previouskey] 
        #print self.persistentDataDict
        
        

        
            
   