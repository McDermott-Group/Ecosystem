# Copyright (C) 2016  Alexander "Daddy" Opremcak
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import h5py
from dateStamp import *
import numpy as np
import string
import inspect

VAR_NAME_INDEX_POS = 0
VAR_SHAPE_INDEX_POS = 1
VAR_TYPE_INDEX_POS = 2
VAR_UNIT_INDEX_POS = 3

EXPECTED_TUPLE_LEN = 4
EXPECTED_TUPLE_TYPES = [str, list, str, str]

ERROR_GRAMMAR = {
    '0':"th",
    '1':"st",
    '2':"nd",
    '3':"rd",
    '4':"th"
}

VALID_DATA_TYPES = ['bool_', 'int8', 'int16', 'int32',
                    'int64', 'uint8', 'uint16', 'uint32',
                    'uint64','int_', 'float16', 'float32',
                    'float64','float_', 'complex64',
                    'complex128', 'complex_']

class dataChest(dateStamp):

  def __init__(self):
    self.cwdPath = "Z:/mcdermott-group/DataChest"
    os.chdir(self.cwdPath)
    self.dateStamp = dateStamp()
    self.currentHDF5Filename = None
    self.readOnlyFlag = False
    self.varDict = {}
    self.varDict["independents"] = {}
    self.varDict["dependents"] ={}
    self.numIndepWrites = 0
    self.numDepWrites = 0

  def ls(self):
    """Lists the contents of the current working directory."""
    cwdContents = os.listdir(self.cwdPath)
    files = []
    folders = []
    for item in cwdContents:
      if not item.startswith('.'): #ignores hidden sys files
        if "." in item:
          files.append(item)
        else:
          folders.append(item)
    files = sorted(files) #alphabetize me captain...
    folders = sorted(folders)
    return [files, folders]

  def cd(self, directoryToMove): #needs to be debugged now that we accept below types
    """Changes the current working directory.""" #accepts single string, path, list
    if isinstance(directoryToMove, str):
      if "/" in directoryToMove:
        path = directoryToMove.split("/")
        print "path=", path
      else:
        path = [directoryToMove]
    elif isinstance(directoryToMove, list):
      path = directoryToMove
    if len(path)>0:
      for ii in range(0, len(path)):
        cwdContents = self.ls()
        if (path[ii] in cwdContents[1]):
          self.cwdPath = self.cwdPath+"/"+path[ii]
          os.chdir(self.cwdPath)
          return self.cwdPath
        elif path[ii]=="..":#should never takes us out of root
          os.chdir("..")
          self.cwdPath = os.getcwd().replace("\\", "/") #unix style paths
          return self.cwdPath
        elif path[ii]=="":
          return self.cwdPath
        else:
          self._dataChestError("Directory does not exist.\r\n\t"+
                               "Directory name provided: "+str(directoryToMove))
          return "Error"
      else:
        return directoryToMove

  def mkdir(self, directoryToMake): #doesn't cd automatically
    """Makes a new directory within the current working directory."""
    dirContents = self.ls()[1]
    if self._formatFilename(directoryToMake) == directoryToMake:
      if directoryToMake not in dirContents:
        os.mkdir(directoryToMake)
        return directoryToMake
      else:
        self._dataChestError("Directory already exists.\r\n\t"+
                             "Directory name provided: "+
                             directoryToMake)
        return "Error"
    else:
      self._dataChestError("Invalid directory name provided.\r\n\t"+
                           "Directory name provided: "+directoryToMake+
                           ".\r\n\t"+ "Suggested name: "+
                           self._formatFilename(directoryToMake))
      return "Error"
    
  def createDataset(self, datasetName, indepVarsList, depVarsList): 
    "Creates a new dataset within the current working directory.""" 
    self.currentHDF5Filename = None #initialized to None
    self.readOnlyFlag = False
    if datasetName != self._formatFilename(datasetName):
      self._dataChestError(("An illegal fileName was provided.\r\n\t"+
                           "Please use only ASCII letters, the\r\n\t"+
                           "digits 0 through 9, and underscores\r\n\t"+
                           "in your dataset names."))
      return "Error"
    elif not self._isVarsListValid(
                                   "independents",
                                   indepVarsList
                                   ) == indepVarsList: 
      return "Error"
    elif not self._isVarsListValid(
                                   "dependents",
                                   depVarsList) == depVarsList:
      return "Error"
    elif self._getVariableNames(indepVarsList+depVarsList)==[]:
      return "Error"
    
    filename = self._generateUniqueFilename(datasetName)
    if len(filename)>0: #generate unique name if not ****
      self.currentFile = h5py.File(self.cwdPath+"/"+filename) #should check for success
      self.currentHDF5Filename = self.cwdPath+"/"+filename  #before setting this
      self.readOnlyFlag = False # newly created files have read and write access

      self.currentFile.create_group("independents") #create indeps group
      self.currentFile.create_group("dependents") #create deps group
      self.currentFile.create_group("parameters") ##create params group

      for varTypes in self.varDict.keys(): # ['independents', 'dependents']
        for varAttrs in self.varDict[varTypes].keys(): # ['shapes', 'units', 'names', 'types']
          varGrp = self.currentFile[varTypes]
          varGrp.attrs[varAttrs] = self.varDict[varTypes][varAttrs] #sets attributes 
        self._initDatasetGroup(varGrp, self.varDict[varTypes]) #init params group within
      self.currentFile.flush()
    else:
      self._dataChestError("Unable to create a unique filename.")
      return "Error"
    
  def addData(self, data):
    """Adds data to the latest dataset created with new.
       Expects data of the form [[indep1_1, indep2_1, dep1_1, dep2_1],
       [indep1_2, indep2_2, dep1_2, dep2_2],...].
    """
    if self.readOnlyFlag == True: 
      self._dataChestError(("You cannot gain write privileges to\r\n\t"+
                           "this file as it was opened read\r\n\t"+
                           "only. Files opened with the\r\n\t"+
                           "openDataset() method are read only\r\n\t"+
                           "by design. You must make a new\r\n\t"+
                           "dataset if you wish to write to one."))
      return "ERROR"
    elif self.currentHDF5Filename is not None:
      if self._isDataValid(data):
        numIndeps = len(self.varDict["independents"]["names"])
        numDeps = len(self.varDict["dependents"]["names"])
        numRows = len(data)
        for rowIndex in range(0, numRows):
          for colIndex in range(0, len(data[rowIndex])):
            if colIndex<numIndeps:
              varGrp = "independents"
              varName = self.varDict[varGrp]["names"][colIndex]
              varData = np.asarray(data[rowIndex][colIndex])
              flattenedVarShape = self._flattenedShape(self.varDict[varGrp]["shapes"][colIndex])[0]
              self._addToDataset(self.currentFile[varGrp][varName],
                                 varData,
                                 flattenedVarShape,
                                 self.numIndepWrites)
            else:
              varGrp = "dependents"
              varName = self.varDict[varGrp]["names"][colIndex-numIndeps]
              varData = np.asarray(data[rowIndex][colIndex])
              flattenedVarShape = self._flattenedShape(self.varDict[varGrp]["shapes"][colIndex-numIndeps])[0]
              self._addToDataset(self.currentFile[varGrp][varName],
                                 varData,
                                 flattenedVarShape,
                                 self.numDepWrites)
          self.numIndepWrites = self.numIndepWrites+ 1 #after the entire column is written to 
          self.numDepWrites = self.numDepWrites+ 1
        self.currentFile.flush()
      else:
        #Invalid data provided and error message will be provided with details
        return False
    else:
      self._dataChestError(("You must create a dataset before\r\n\t"+
                           "attempting to write. Datasets are\r\n\t"+
                           "created using the createDataset()\r\n\t"+
                           "method of this class."))
      return False

  def openDataset(self, name):
    """Opens a dataset within the current working directory if it exists"""
    if '.hdf5' not in name: #adds file extension if emitted.
      name = name+".hdf5"
    #print "Name=", name
    #print "self.cwdPath=", self.cwdPath
    files = self.ls()[0]
    if name in files:
      if hasattr(self, 'currentFile'):
        self.currentFile.close() #close current file if existent
      self.currentFile = h5py.File(name,'r') #opened read only
      self.readOnlyFlag = True
      self.currentHDF5Filename = self.cwdPath + "/" + name
      
      for keys in self.currentFile["independents"].attrs.keys():
        self.varDict["independents"][str(keys)] = self.currentFile["independents"].attrs[keys].tolist()
      for keys in self.currentFile["dependents"].attrs.keys():
        self.varDict["dependents"][str(keys)] = self.currentFile["dependents"].attrs[keys].tolist()
        
    else:
      self.currentHDF5Filename = None
      self._dataChestError(("File not found, please cd into the\r\n\t"+
                           "directory with the desired dataset.\r\n\t"+
                           "If you are receiving this inerror,\r\n\t"+
                           "please use the ls() method to\r\n\t"+
                           "confirm existence and report the\r\n\t"+
                           "error on github."))
      return "Error"
    
  def getData(self):
    # get data 1 var at a time, dechunk it and return in original format
    if self.currentHDF5Filename is not None:  #is this extremely inefficient for 1-D Data??
      dataDict = {}
      for varTypes in self.varDict.keys():
        for variables in self.currentFile[varTypes].keys():
          varGrp = self.currentFile[varTypes]
          fullDataSet = varGrp[variables].value
          originalShape = varGrp[variables].attrs["shapes"]
          chunkSize = self._flattenedShape(originalShape)[0]
          totalLen = varGrp[variables].shape[0]
          numChunks = totalLen/chunkSize
          dataDict[variables]=[]
          for ii in range(0, numChunks):
            chunk =  np.asarray(fullDataSet[ii*chunkSize:(ii+1)*chunkSize])
            if len(originalShape)>1:
              chunk = np.reshape(chunk, tuple(originalShape))
            dataDict[variables].append(chunk.tolist())

      #load parameters here perhaps
      data = []
      allVars = (self.varDict["independents"]["names"] +
                 self.varDict["dependents"]["names"])
      for ii in range(0,numChunks):
        row = []
        for jj in range(0,len(allVars)):
          row.append(dataDict[allVars[jj]][ii])
        data.append(row)
      return data
    else:
      self._dataChestError(("No file is currently selected. Please select a file\r\n\t"+
             "using either the openDataset method to open an existing\r\n\t"+
             "set or with the createDataset method."))
      return False

  def getVariables(self):
    if self.currentHDF5Filename is not None:
      indeps = self._makeVarListFromDict(self.currentFile["independents"])
      deps = self._makeVarListFromDict(self.currentFile["dependents"])
      return [indeps, deps]
    else:
      self._dataChestError(("No file is currently selected. Please select a file\r\n\t"+
             "using either the openDataset method to open an existing\r\n\t"+
             "set or with the createDataset method before attempting to getVariables."))
      return None

  def getDatasetName(self):
    if self.currentHDF5Filename is not None:
      return self.currentHDF5Filename.split("/")[-1]
    else:
      return None

  def cwd(self):
    return self.cwdPath

  def addParameter(self, parameterName, parameterValue): 
    if self.readOnlyFlag == True: 
      self._dataChestError(("You cannot add parameters to this file for it was\r\n\t"+
      "opened read only. Files opened with the openDataset() method of \r\n\t"+
      "this class are read only by design. You must make a new dataset \r\n\t"+
      "if you wish to add parameters to one."))
    elif self.currentHDF5Filename is not None:
      if self._isParameterValid(parameterName, parameterValue):
        self.currentFile["parameters"].attrs[parameterName] = parameterValue
        self.currentFile.flush()
      else:
        return False
    else:
      self._dataChestError(("No file is currently selected. Please create a file\r\n\t"+
             "using the createDataset method before attempting to use add parameters."))      
      
  def getParameter(self, parameterName):
    if self.currentHDF5Filename is not None:
      if parameterName in self.currentFile["parameters"].attrs.keys():
        return self.currentFile["parameters"].attrs[parameterName]
      else:
        self._dataChestError("parameter not found!.")
    else:
      self._dataChestError(("No file is currently selected. Please select a file\r\n\t"+
             "using either the openDataset method to open an existing\r\n\t"+
             "set or with the createDataset method."))

  def getParameterList(self):
    if self.currentHDF5Filename is not None:
      return self.currentFile["parameters"].attrs.keys()
    else:
      self._dataChestError(("No file is currently selected. Please select a file\r\n\t"+
             "using either the openDataset method to open an existing\r\n\t"+
             "set or with the createDataset method."))

  def _generateUniqueFilename(self, datasetName):
    maxTries = 100
    uniquenessFlag = False
    ii = 0
    uniqueName = ""
    while ii<maxTries and uniquenessFlag == False:
      if ii == 0:
        if (self.dateStamp.dateStamp()+"_"+datasetName+".hdf5") not in self.ls()[0]:
          uniqueName = (self.dateStamp.dateStamp()+"_"+datasetName+".hdf5")
          uniquenessFlag = True
        else:
          ii = ii + 1
      else:
        if (self.dateStamp.dateStamp()+"_"+str(ii)+"_"+datasetName+".hdf5") not in self.ls()[0]:
          uniqueName = (self.dateStamp.dateStamp()+"_"+str(ii)+"_"+datasetName+".hdf5")
          uniquenessFlag = True
        else:
          ii = ii + 1
    return uniqueName

  def _updateVariableDict(self, varDict, varList):
    varDict["names"] = self._getVariableNames(varList)
    varDict["shapes"] = self._getVariableShapes(varList)
    varDict["types"] = self._getVariableTypes(varList)
    varDict["units"] = self._getVariableUnits(varList)
    return

  def _makeVarListFromDict(self, varDict):
    names = varDict.attrs["names"]
    shapes = varDict.attrs["shapes"]
    types = varDict.attrs["types"]
    units = varDict.attrs["units"]
    varList = []
    for ii in range(0, len(names)):
      varList.append((names[ii], shapes[ii].tolist(),types[ii],units[ii]))
    return varList
    
  def _formatFilename(self, fileName, additionalChars=None): #private method
      """Take a string and return a valid filename constructed from the string."""
      if additionalChars is None:
        valid_chars = "_%s%s" % (string.ascii_letters, string.digits) #maybe remove dot, dash, and () ??
        filename = ''.join(c for c in fileName if c in valid_chars)
      else:
        valid_chars = "_"+additionalChars
        valid_chars = valid_chars+"%s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in fileName if c in valid_chars)
      return filename

  def _areTypesValid(self, dataTypes):
    for ii in range(0, len(dataTypes)):
      if dataTypes[ii] not in VALID_DATA_TYPES:
        self._dataChestError("An invalid datatype was detected.\r\n\t"+
                             "Type provided="+str(dataTypes[ii])+"\r\n\t"+
                             "Valid types="+str(VALID_DATA_TYPES))
        return False
    return True
          
  def _getVariableNames(self, varsList): # this and the two that follow could possible be combined into 1
    varNames = []
    for ii in range(0, len(varsList)):
      if self._formatFilename(varsList[ii][VAR_NAME_INDEX_POS]) == varsList[ii][VAR_NAME_INDEX_POS]:
        varNames.append(varsList[ii][VAR_NAME_INDEX_POS])
      else:
        self._dataChestError("Invalid variable name was provided.\r\n\t"+
                             "Name provided: "+varsList[ii][VAR_NAME_INDEX_POS]+".\r\n\t"+
                             "Suggested alternative: "+self._formatFilename(varsList[ii][VAR_NAME_INDEX_POS]))
        return []
    if len(varNames) != len(set(varNames)):
      self._dataChestError("All variable names must be distinct.")
      varNames = []                    
    return varNames

  def _getVariableShapes(self, varsList):
    varShapes= []
    for ii in range(0, len(varsList)):
      if len(varsList[ii][VAR_SHAPE_INDEX_POS])>0:  #shapes must be of form [num1], [num1, num2], ...
        for kk in range(0, len(varsList[ii][VAR_SHAPE_INDEX_POS])):
          if not isinstance(varsList[ii][VAR_SHAPE_INDEX_POS][kk], int):
            self._dataChestError("Non integer shape dimensions are not allowed.")
            return []
          elif varsList[ii][VAR_SHAPE_INDEX_POS][kk]<=0:
            self._dataChestError("Zero or negative shape dimensions are not allowed.")
            return []
      else:
        self._dataChestError("Shapes cannot be the empty list as this has no meaning")
      varShapes.append(varsList[ii][VAR_SHAPE_INDEX_POS])
    return varShapes

  def _getVariableTypes(self, varsList):
    varTypes= []
    for ii in range(0, len(varsList)):
      varTypes.append(varsList[ii][VAR_TYPE_INDEX_POS])
    if not self._areTypesValid(varTypes):
      varTypes = []
    return varTypes

  def _getVariableUnits(self, varsList):
    varTypes= []
    for ii in range(0, len(varsList)):
      varTypes.append(varsList[ii][VAR_UNIT_INDEX_POS])
    return varTypes

  def _initDatasetGroup(self, group, varDict):
    self.numIndepWrites = 0
    self.numDepWrites = 0
    for ii in range(0, len(varDict["names"])):
      #creates each dataset, set datatype, chunksize, maxshape, fillvalue
      dset = group.create_dataset(varDict["names"][ii],
                                  tuple(self._flattenedShape(varDict["shapes"][ii])),
                                  dtype=varDict["types"][ii],
                                  chunks=tuple(self._flattenedShape(varDict["shapes"][ii])),
                                  maxshape=(None,),
                                  fillvalue=np.nan)
      #stores name, shape, type, and units as attributes for this dataset (sort of redundant as this is done at the varType group level)
      for keys in varDict:
        if isinstance(varDict[keys][ii], str):
          dset.attrs[keys] = unicode(varDict[keys][ii], "utf-8")
        elif isinstance(varDict[keys][ii], list):
          dset.attrs[keys] = varDict[keys][ii]
        else:
          self._dataChestError("Unrecognized type was receieved. Please report this message on github.")

  def _addToDataset(self, dset, data, chunkSize, numWrites):
    if numWrites == 0:
      data = np.reshape(data, (chunkSize,))
      dset[:chunkSize] = data
    else:
      data = np.reshape(data, (chunkSize,))
      dset.resize((dset.shape[0]+chunkSize,))
      dset[-chunkSize:] = data

  def _isDataValid(self, data):
    if isinstance(data, list): # checks that its a list
      numRows = len(data)
      if numRows>0: # if length nonzero proceed to check tuples
        for ii in range(0, numRows):
          if not (isinstance(data[ii], list) or isinstance(data[ii], np.ndarray)): #each entry should be 
            self._dataChestError(("For row ="+str(ii)+" of the data entered is not a list. \r\n\t"+
            "Data entered should be of the form: \r\n\t"+
            "[[indep1_0, indep2_0, dep1_0, dep2_0], ... \r\n\t"+
            "[indep1_n, indep2_n, dep1_n, dep2_n]] \r\n\t"+
            "where [indep1_m, indep2_m, dep1_m, dep2_m] \r\n\t"+
            "is the m'th row of your data set."))
            return False
          else: #check that entries
            # tuple form (dep1, dep2, ...,indep1, indep2,...) where dep(indep) are of the shape specified by new
            if not self._isRowValid(data[ii]):
              return False
      else: # [] is not a valid dataset
        self._dataChestError("Vacuous datasets are invalid.")
        return False
    else:
      self._dataChestError("The dataset provided was not of type list.")
      return False
    return True

  def _isRowValid(self, dataList):
    numIndeps = len(self.varDict["independents"]["names"])
    numDeps = len(self.varDict["dependents"]["names"])
    if len(dataList) == (numIndeps+numDeps):
      for ii in range(0, (numIndeps+numDeps)):
        if self._isColumnHomogeneousList(dataList[ii]):
          array = np.asarray(dataList[ii])        
          #check that all subelements are lists or nparrays ***
          if ii < numIndeps:
            if array.shape != tuple(self.varDict["independents"]["shapes"][ii]):
              self._dataChestError("Data shapes do not match for the independent variable data.\r\n\t"+
                                   "Expected shape: "+str(tuple(self.varDict["independents"]["shapes"][ii]))+".\r\n\t"+
                                   "Received shape: "+str(array.shape))
              return False
            elif array.dtype.name != self.varDict["independents"]["types"][ii]:
              self._dataChestError("Types do not match for independents")
              return False           
          else:
            if array.shape != tuple(self.varDict["dependents"]["shapes"][ii-numIndeps]):
              self._dataChestError("Data shapes do not match for the independent variable data.\r\n\t"+
                                   "Expected shape: "+str(tuple(self.varDict["dependents"]["shapes"][ii-numIndeps]))+".\r\n\t"+
                                   "Received shape: "+str(array.shape))
              return False
            elif array.dtype.name != self.varDict["dependents"]["types"][ii-numIndeps]:
              self._dataChestError("Types do not match for dependents")  #this will most likely be our biggest problem
              return False
        else:
          self._dataChestError("The column elements (along with all subelements)\r\n\t"+
                               "of a row must be of type list or a numpy ndarray.")
          return False
    else:
      self._dataChestError("Incorrect number of data columns provided.")
      return False
    return True

  def _flattenedShape(self, shapeList):
    totalDim = 1
    for ii in range(0, len(shapeList)):
      totalDim = totalDim*shapeList[ii]
    return [totalDim]
      
  def _isVarsListValid(self, varType, varsList): #all labels need different names
    if isinstance(varsList, list):
      if len(varsList) == 0:
        self._dataChestError("A data set with no "+varType+" has no meaning.")
        return "Error"
      for ii in range(0, len(varsList)): #checks validity of each dep or indep tuple
        if not self._isTupleValid(varType, varsList[ii]):
          return "Error"
      self._updateVariableDict(self.varDict[varType], varsList)
      for varAttributes in self.varDict[varType].keys():
        if len(self.varDict[varType][varAttributes])==0:
          #self._dataChestError("Invalid entry detected for key=" + varAttributes)
          return "Error"
      return varsList
    else:
      self._dataChestError("Expecting list of "+varType+" variables.")
      return "Error"

  def _isTupleValid(self, varType, tupleValue):
    
    if not isinstance(tupleValue, tuple): #Checks if it is actually a tuple
      self._dataChestError("Expecting list elements to be of type tuple")
      return False
    elif not(len(tupleValue) == EXPECTED_TUPLE_LEN): # Checks tuple is of expected length
      self._dataChestError("Expecting tuple elements to be of length "+
                           str(EXPECTED_TUPLE_LEN))
      return False
    
    for jj in range(0, len(EXPECTED_TUPLE_TYPES)):  #Loops over all tuple elements
      if not isinstance(tupleValue[jj], EXPECTED_TUPLE_TYPES[jj]): #Checks that the type is correct
        self._dataChestError(("In the "+varType+" variables list,\r\n\t"+
                              "for the tuple =" + str(tupleValue)+",\r\n\t"+
                              "the "+str(jj)+ERROR_GRAMMAR[str(jj)]+
                              " element should be of\r\n\t"+
                              str(EXPECTED_TUPLE_TYPES[jj])))
        return False
    return True

  def _isParameterValid(self, parameterName, parameterValue):

    validTypes = (int, long, float, complex, bool,
                  list, np.ndarray, str, unicode)
    if isinstance(parameterName, str):
      if self._formatFilename(parameterName, " ") != parameterName:
        self._dataChestError("Invalid parameter name provided.")
        return False
      elif not isinstance(parameterValue, validTypes): 
        self._dataChestError("Invalid datatype parameter\r\n\t"+
                             "was provided.\r\n\t"+
                             "Accepted types: int, long, float,\r\n\t"+
                             "complex, bool, list, np.ndarray,\r\n\t"+
                             "str, unicode.\r\n\t"+
                             "Type provided=", type(parameterValue))
        #lists must be of one type or else type conversion occurs
        #[12.0, 5e-67, "stringy"] --> ['12.0', '5e-67', 'stringy']                                   
        return False
      elif parameterName in self.currentFile["parameters"].attrs.keys():
        self._dataChestError("Parameter name already exists. \r\n\t"+
                             "Parameter values cannot be overwritten.")
        return False
      else:
        return True
    else:
      self._dataChestError("Parameter names must be of type str.")
      return False

  def _isColumnHomogeneousList(self, colVal):
    tup = None
    checked = []
    for value in np.ndenumerate(colVal):
        tup = value[0][:-1]
        for ii in range(0, len(tup)):
          if tup not in checked:
            checked.append(tup)
            if not isinstance(self.valByTup(tup, colVal),
                              (list, np.ndarray)):
              return False
            tup = tup[:-1]
    return True

  def valByTup(self, tupl, array):
      answer = array
      for i in tupl:
          answer = answer[i]
      return answer

  def _dataChestError(self, errorMessage):
    fxnName = inspect.stack()[1][3]
    errMessage = ("\t***ERROR*** "+fxnName+"():\r\n\t"+errorMessage)
    print errMessage

#automatically close file when new one is created or object is killed
#make sure that files are always closed and we dont run into file already open conflicts
##TODO:
    ##cut lines to <=72 characters
    ##add dictionary parameter capabilities ***
    ##test for speed, 1D case in particular shape = [1]
    ##over night writes both locally and on afs data corruption tests
