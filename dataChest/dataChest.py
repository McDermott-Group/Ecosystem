# Copyright (C) 2016  Alexander Opremcak
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
from dateStamp import dateStamp
import numpy as np
import string
import inspect
import time
import gc
import re

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
                    'complex128', 'complex_', 'utc_datetime', 'string']

class dataChest(dateStamp):

  def __init__(self):
    self.root = "C:/DataChest"
    self.cwdPath = self.root #initialized to root to start
    os.chdir(self.cwdPath)
    self.dateStamp = dateStamp()
    self.currentHDF5Filename = None
    self.readOnlyFlag = False
    self.varDict = {}
    self.varDict["independents"] = {}
    self.varDict["dependents"] ={}
    self.numIndepWrites = 0
    self.numDepWrites = 0

  def ls(self): #good
    """Lists the contents of the current working directory."""
    cwdContents = os.listdir(self.cwdPath)
    files = []
    folders = []
    for item in cwdContents:
      if not item.startswith('.'): #ignore hidden sys files
        if "." in item:
          files.append(item)
        else:
          folders.append(item)
    files = sorted(files) #alphabetize for readibility
    folders = sorted(folders)
    return [files, folders]

  def cd(self, directoryToMove): #TODO: never let this take you out of root
    """Changes the current working directory."""
    if isinstance(directoryToMove, str):
      path = [directoryToMove]
    elif isinstance(directoryToMove, list):
      path = directoryToMove
    else:
      self._dataChestError("Acceptable argument types are string and list only.")
      return "Error"
        
    if len(path)>0:
      for ii in range(0, len(path)):
        cwdContents = self.ls()
        if (path[ii] in cwdContents[1]):
          self.cwdPath = self.cwdPath+"/"+path[ii]
          os.chdir(self.cwdPath)
        elif path[ii]=="..":
          os.chdir("..")
          if len(path)>1:
            self._dataChestError("Received .. in the middle of an array path.", warning=True)
          self.cwdPath = os.getcwd().replace("\\", "/") #unix style paths
        elif path[ii]=="":
          if len(path)>1:
            self._dataChestError("Received an empty string in the middle of an array path.", warning=True)
          os.chdir(self.root)
          self.cwdPath = os.getcwd().replace("\\", "/")
        else:
          self._dataChestError("Directory does not exist.\r\n\t"+
                               "Directory name provided: "+str(directoryToMove))
          return "Error"
      return self.cwdPath
    else:
      return directoryToMove

  def mkdir(self, directoryToMake): #good
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
    
  def createDataset(self, datasetName, indepVarsList, depVarsList): #treat self.dataCategory consistently
    "Creates a new dataset within the current working directory.""" 
    self.currentHDF5Filename = None
    self.readOnlyFlag = False
    self.dataCategory = None
    if datasetName != self._formatFilename(datasetName):
      self._dataChestError(("An illegal fileName was provided.\r\n\t"+
                           "Please use only ASCII letters, the\r\n\t"+
                           "digits 0 through 9, and underscores\r\n\t"+
                           "in your dataset names."))
      return "Error"
    elif not self._isVarsListValid("independents", indepVarsList): 
      return "Error"
    elif not self._isVarsListValid("dependents", depVarsList):
      return "Error"
    elif self._getVariableNames(indepVarsList+depVarsList)==[]:
      return "Error"
    
    filename = self._generateUniqueFilename(datasetName)
    if len(filename)>0:
      self.dataCategory = self._categorizeDataset(self.varDict)
      self._initDataset(self.varDict, filename)
    else:
      self._dataChestError("Unable to create a unique filename.")
      return "Error"

  def addData(self, data): #clean and design around string and datetime objects
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
        indepShapes = self.varDict["independents"]["shapes"]
        depShapes = self.varDict["dependents"]["shapes"]
        if self.dataCategory == "Arbitrary Type 1":
          varData = np.asarray(data)
          for colIndex in range(0, numIndeps+numDeps):
            column = [data[ii][colIndex] for ii in range(0, len(data))]
            column = np.asarray(column)
            if colIndex<numIndeps:
              varGrp = "independents"
              varName = self.varDict[varGrp]["names"][colIndex]
              flattenedVarShape = len(column)
              self._addToDataset(self.currentFile[varGrp][varName],
                                 column,
                                 flattenedVarShape,
                                 self.numIndepWrites)
            else:
              varGrp = "dependents"
              varName = self.varDict[varGrp]["names"][colIndex-numIndeps]
              flattenedVarShape = len(column)
              dat = varData[:,colIndex]
              self._addToDataset(self.currentFile[varGrp][varName],
                                 column,
                                 flattenedVarShape,
                                 self.numDepWrites)
          self.numIndepWrites = self.numIndepWrites+len(dat) #after the entire column is written to 
          self.numDepWrites = self.numDepWrites+len(dat)
        else:
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
        print "Invalid data provided and error message will be provided with details"
        return "ERROR"
    else:
      self._dataChestError(("You must create a dataset before\r\n\t"+
                           "attempting to write. Datasets are\r\n\t"+
                           "created using the createDataset()\r\n\t"+
                           "method of this class."))
      return "ERROR"
    return True

  def openDataset(self, filename): #treat self.dataCategory consistently
    """Opens a dataset within the current working directory if it exists"""
    if '.hdf5' not in filename: #adds file extension if emitted
      filename = filename+".hdf5"
    existingFiles = self.ls()[0]
    if filename in existingFiles:
      if hasattr(self, 'currentFile'):
        self.currentFile.close() #close current file if existent
      self.currentFile = h5py.File(filename,'r') #opened read only
      self.readOnlyFlag = True
      self.currentHDF5Filename = self.cwdPath + "/" + filename
      
      for keys in self.currentFile["independents"].attrs.keys():
        self.varDict["independents"][str(keys)] = self.currentFile["independents"].attrs[keys].tolist()
      for keys in self.currentFile["dependents"].attrs.keys():
        self.varDict["dependents"][str(keys)] = self.currentFile["dependents"].attrs[keys].tolist()
        
      gc.collect()
        
    else:
      self.currentHDF5Filename = None
      self._dataChestError(("File not found, please cd into the\r\n\t"+
                           "directory with the desired dataset.\r\n\t"+
                           "If you are receiving this inerror,\r\n\t"+
                           "please use the ls() method to\r\n\t"+
                           "confirm existence and report the\r\n\t"+
                           "error on github."))
      return "Error"
    
  def getData(self): #is this extremely inefficient for 1-D Data??
    # get data 1 var at a time, dechunk it and return in original format
    if self.currentHDF5Filename is not None:
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
            if len(originalShape)>1 or originalShape!=[1]:
              chunk = np.reshape(chunk, tuple(originalShape))
              dataDict[variables].append(chunk.tolist())
            else:
              dataDict[variables].append(chunk[0])    
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

  def _initDataset(self, varDict, filename):

    self.numIndepWrites = 0
    self.numDepWrites = 0
    
    self.currentFile = h5py.File(self.cwdPath+"/"+filename) #should check for success
    self.currentHDF5Filename = self.cwdPath+"/"+filename  #before setting this
    self.readOnlyFlag = False # newly created files have read and write access
    
    #create the following groups within file:
    self.currentFile.create_group("independents")
    self.currentFile.create_group("dependents")
    self.currentFile.create_group("parameters")

    self.currentFile.attrs["Data Category"] = self.dataCategory

    for varTypes in varDict.keys(): #keys=['independents', 'dependents']
      for varAttrs in varDict[varTypes].keys():# keys =['shapes','units','names','types']
        varGrp = self.currentFile[varTypes]
        varGrp.attrs[varAttrs] = varDict[varTypes][varAttrs] #sets attributes 
      self._initDatasetGroup(varGrp, varDict[varTypes])
    self.currentFile.flush()
    

  def _initDatasetGroup(self, group, varDict):
    
    for ii in range(0, len(varDict["names"])):
      #creates each dataset, set datatype, chunksize, maxshape, fillvalue
      if varDict["types"][ii] == 'string' or varDict["types"][ii] == 'utc_datetime':
        dataType = h5py.special_dtype(vlen=str)
        fillVal = None
        dset = group.create_dataset(varDict["names"][ii],
                                    tuple(self._flattenedShape(varDict["shapes"][ii])),
                                    dtype=dataType,
                                    chunks=tuple(self._flattenedShape(varDict["shapes"][ii])),
                                    maxshape=(None,))
      else:
        dataType = varDict["types"][ii]
        fillVal = np.nan
        dset = group.create_dataset(varDict["names"][ii],
                                    tuple(self._flattenedShape(varDict["shapes"][ii])),
                                    dtype=dataType,
                                    chunks=tuple(self._flattenedShape(varDict["shapes"][ii])),
                                    maxshape=(None,),
                                    fillvalue=np.nan)
  
      #stores name, shape, type, and units as attributes for this dataset
      #(sort of redundant as this is done at the varType group level)???
      for keys in varDict:
        if isinstance(varDict[keys][ii], str):
          dset.attrs[keys] = unicode(varDict[keys][ii], "utf-8")
        elif isinstance(varDict[keys][ii], list):
          dset.attrs[keys] = varDict[keys][ii]
        else:
          self._dataChestError("Unrecognized type was receieved. Please report this message on github.")

  def _generateUniqueFilename(self, datasetName):
    uniquenessFlag = False
    uniqueName = ""
    maxTries = 100
    ii = 0
    existingNames = self.ls()[0]
    while ii<maxTries and uniquenessFlag == False:
      if ii == 0:
        uniqueName = (self.dateStamp.dateStamp()+"_"+datasetName+".hdf5")
      else:
        uniqueName = (self.dateStamp.dateStamp()+"_"+str(ii)+"_"+datasetName+".hdf5") 

      if uniqueName not in existingNames:
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

  def _addToDataset(self, dset, data, chunkSize, numWrites):
    if numWrites == 0:
      data = np.reshape(data, (chunkSize,))
      if dset.shape[0] == 1 and chunkSize !=1: #accounts for 1D arbitrary data I believe
        dset.resize((chunkSize,))
      dset[:chunkSize] = data
    else:
      data = np.reshape(data, (chunkSize,))
      dset.resize((dset.shape[0]+chunkSize,))
      dset[-chunkSize:] = data

  def _isDataValid(self, data):
    if isinstance(data, list): # checks that its a list
      numRows = len(data)
      if numRows>0: # if length nonzero proceed to check tuples
        if self.dataCategory == "Arbitrary Type 1":
          if self._isDataFormatArbType1(data, self.varDict):
            return True
          else:
            return False
        elif self.dataCategory == "Arbitrary Type 2":
          if self._isDataFormatArbType2(data, self.varDict):
            return True
          else:
            return False
        elif self.dataCategory == "1D Scan":
          if self._isDataFormat1DScan(data, self.varDict):
            return True
          else:
            return False
        elif self.dataCategory == "2D Scan":
          if self._isDataFormat2DScan(data, self.varDict):
            return True
          else:
            return False
        else:
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
##        if self._isColumnHomogeneousList(dataList[ii]):  #check that all subelements are lists or nparrays ***
        array = np.asarray(dataList[ii])        
        if ii < numIndeps:
          if self.varDict["independents"]["shapes"][ii]==[1]:
            if array.shape!=():
              self._dataChestError("Data of shape [1] should not be placed as an array.")
              return False
          elif array.shape != tuple(self.varDict["independents"]["shapes"][ii]):
            self._dataChestError("Data shapes do not match for the independent variable data.\r\n\t"+
                                 "Expected shape: "+str(tuple(self.varDict["independents"]["shapes"][ii]))+".\r\n\t"+
                                 "Received shape: "+str(array.shape))
            return False
          elif self.varDict["independents"]["types"][ii] == 'string':
            if not self._isArrayAllStrings(array):
              return False
          elif self.varDict["independents"]["types"][ii] == 'utc_datetime':
            if not self._isArrayAllUTCDatestamps(array):
              return False
          elif array.dtype.name != self.varDict["independents"]["types"][ii]:
            self._dataChestError("Types do not match for independents")
            return False           
        else:
          if self.varDict["dependents"]["shapes"][ii-numIndeps]==[1]:
            if array.shape!=():
              self._dataChestError("Data of shape [1] should not be placed as an array.")
              return False
          elif array.shape != tuple(self.varDict["dependents"]["shapes"][ii-numIndeps]):
            self._dataChestError("Data shapes do not match for the independent variable data.\r\n\t"+
                                 "Expected shape: "+str(tuple(self.varDict["dependents"]["shapes"][ii-numIndeps]))+".\r\n\t"+
                                 "Received shape: "+str(array.shape))
            return False
          elif self.varDict["dependents"]["types"][ii-numIndeps] == 'string':
            if not self._isArrayAllStrings(array):
              return False
          elif self.varDict["dependents"]["types"][ii-numIndeps] == 'utc_datetime':
            if not self._isArrayAllUTCDatestamps(array):
              return False
          elif array.dtype.name != self.varDict["dependents"]["types"][ii-numIndeps]:
            self._dataChestError("Types do not match for dependents")  #this will most likely be our biggest problem
            return False
##        else:
##          self._dataChestError("The column elements (along with all subelements)\r\n\t"+
##                               "of a row must be of type list or a numpy ndarray.")
##          return False
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
        return False
      for ii in range(0, len(varsList)): #checks validity of each dep or indep tuple
        if not self._isTupleValid(varType, varsList[ii]):
          return False
      self._updateVariableDict(self.varDict[varType], varsList)
      for varAttributes in self.varDict[varType].keys():
        if len(self.varDict[varType][varAttributes])==0:
          return False
      return True
    else:
      self._dataChestError("Expecting list of "+varType+" variables.")
      return False

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

  def _dataChestError(self, errorMessage, warning = False):
    fxnName = inspect.stack()[1][3]
    if warning == False:
      errMessage = ("\t***ERROR*** "+fxnName+"():\r\n\t"+errorMessage)
    else:
      errMessage = ("\t***WARNING*** "+fxnName+"():\r\n\t"+errorMessage)
    print errMessage

  def _isStringUTCFormat(self, dateStr):
    RE = re.compile(r'^\d{4}-\d{2}-\d{2}[T]\d{2}:\d{2}:\d{2}[.]\d{6}$')
    return bool(RE.search(dateStr))

  def _categorizeDataset(self, varDict):
    
    indepShapes = varDict["independents"]["shapes"]
    depShapes = varDict["dependents"]["shapes"]
    if self._isDataShapeArbType1(indepShapes, depShapes):
      return "Arbitrary Type 1"
    elif self._isDataShapeArbType2(indepShapes, depShapes):
      return "Arbitrary Type 2"
    elif self._isDataShape1DScan(indepShapes, depShapes):
      return "1D Scan"
    elif self._isDataShape2DScan(indepShapes, depShapes):
      return "2D Scan"
    else:
      return "Other"

  def _isDataShapeArbType1(self, indepShapes, depShapes):
    
    allShapes = indepShapes+depShapes
    for shape in allShapes:
      if shape != [1]:
        return False
    return True

  def _isDataFormatArbType1(self, data, varDict):
    indepShapes = varDict["independents"]["shapes"]
    depShapes = varDict["dependents"]["shapes"]

    indepTypes = varDict["independents"]["types"]
    depTypes = varDict["dependents"]["types"]
    types = indepTypes + depTypes
    
    dataShape = np.asarray(data).shape
    totalNumVars = len(indepShapes+depShapes)
    if len(dataShape) != 2:
      return False
    elif dataShape[1] != totalNumVars:
      return False

    for colIndex in range(0, totalNumVars):
        column = [data[ii][colIndex] for ii in range(0, len(data))]
        column = np.asarray(column)
        columnShape = column.shape
        dtype = column.dtype.name
        if len(columnShape)!=1:
          return False
        elif types[colIndex] == 'string':
          if not self._isArrayAllStrings(column):
            return False
        elif types[colIndex] == 'utc_datetime':
          if not self._isArrayAllUTCDatestamps(column):
            return False
        elif dtype != types[colIndex]:
          return False
    return True

  def _isArrayAllStrings(self, array):
    for ii in range(0, len(array)):
      if not isinstance(array[ii], str):
        print
        return False
    return True

  def _isArrayAllUTCDatestamps(self, array):
    for ii in range(0, len(array)):
      if not self._isStringUTCFormat(array[ii]):
        return False
    return True

  def _isDataFormatArbType2(self, data, varDict):
    indepShapes = varDict["independents"]["shapes"]
    depShapes = varDict["dependents"]["shapes"]

    indepTypes = varDict["independents"]["types"]
    depTypes = varDict["dependents"]["types"]
    types = indepTypes + depTypes
    
    dataShape = np.asarray(data).shape
    totalNumVars = len(indepShapes+depShapes)
    if len(dataShape) != 3:  # (1,totalNumVars,lengthOfDataArray)
      return False
    elif dataShape[1] != totalNumVars:
      return False
    elif dataShape[2] < 2: #==> option 1 or mishapen
      return False

    numRows = dataShape[0]
    numColumns = dataShape[1]
    for rowIndex in range(0, numRows):
      for colIndex in range(0, numColumns):
          column = data[rowIndex][colIndex]
          column = np.asarray(column)
          columnShape = column.shape
          dtype = column.dtype.name
          if types[colIndex] == 'string':
            if not self._isArrayAllStrings(column):
              return False
          elif types[colIndex] == 'utc_datetime':
            if not self._isArrayAllUTCDatestamps(column):
              return False
          elif dtype != types[colIndex]:
            return False
      return True

  def _isDataFormat1DScan(self, data, varDict): #column shape must match
    indepShapes = varDict["independents"]["shapes"]
    depShapes = varDict["dependents"]["shapes"]
    shapes = indepShapes + depShapes

    indepTypes = varDict["independents"]["types"]
    depTypes = varDict["dependents"]["types"]
    types = indepTypes + depTypes
    
    dataShape = np.asarray(data).shape
    totalNumVars = len(indepShapes+depShapes)
    if len(dataShape) != 2:  # (1,totalNumVars,lengthOfDataArray)
      return False
    elif dataShape[1] != totalNumVars:
      return False
    
    numRows = dataShape[0]
    numColumns = dataShape[1]
    for rowIndex in range(0, numRows):
      for colIndex in range(0, numColumns):
          column = data[rowIndex][colIndex]
          column = np.asarray(column) #fails to be casted [1.0, [2.0]]
          columnShape = column.shape
          dtype = column.dtype.name
          if colIndex == 0 and columnShape != (2,):
            return False
          elif types[colIndex] == 'string':
            if not self._isArrayAllStrings(column):
              return False
          elif types[colIndex] == 'utc_datetime':
            if not self._isArrayAllUTCDatestamps(column):
              return False
          elif dtype != types[colIndex]:
            return False
          elif colIndex>1 and (len(columnShape)!=1 or columnShape[0]!=shapes[colIndex][0]):
            return False
          elif colIndex>2 and columnShape != lastShape:
            return False
          lastShape = column.shape
      return True

  def _isDataFormat2DScan(self, data, varDict): #column shape must match
    indepShapes = varDict["independents"]["shapes"]
    depShapes = varDict["dependents"]["shapes"]
    shapes = indepShapes + depShapes

    indepTypes = varDict["independents"]["types"]
    depTypes = varDict["dependents"]["types"]
    types = indepTypes + depTypes
    
    totalNumVars = len(indepShapes+depShapes)
    numRows = len(data)
    if numRows < 1:
      return False
    elif len(indepShapes)!=2:
      return False

    for rowIndex in range(0, numRows):
      row = data[rowIndex]
      if len(row) != totalNumVars:
        return False
      if not ((np.asarray(row[0]).shape==() and np.asarray(row[1]).shape==(2,)) or (np.asarray(row[0]).shape==(2,) and np.asarray(row[1]).shape==())):
        return False        
      for colIndex in range(0, totalNumVars):
        if colIndex > 1:
          if len(np.asarray(row[colIndex]).shape)!=1 or np.asarray(row[colIndex]).shape[0]!=shapes[colIndex][0]:
            return False
          elif types[colIndex] == 'string':
            if not self._isArrayAllStrings(column):
              return False
          elif types[colIndex] == 'utc_datetime':
            if not self._isArrayAllUTCDatestamps(column):
              return False
          elif np.asarray(row[colIndex]).dtype.name != types[colIndex]:
            return False
      return True
  
  def _isDataShapeArbType2(self, indepShapes, depShapes):
    
    allShapes = indepShapes+depShapes
    lastShape = None
    for ii in range(0,len(allShapes)):
      if ii > 0:
        if allShapes[ii] != lastShape:
          return False
        elif allShapes[ii] == [1]:
          return False
      lastShape = allShapes[ii]
    return True

  def _isDataShape1DScan(self, indepShapes, depShapes):
    
    if len(indepShapes)!=1:
      return False
    allShapes = indepShapes+depShapes
    for ii in range(0,len(allShapes)):
      if ii == 0 and allShapes[ii] != [2]:
        return False
      elif len(allShapes[ii])!=1 or allShapes[ii]<2:
        return False
      elif ii>1 and allShapes[ii] != lastShape:
        return False
      lastShape = allShapes[ii]
    return True

  def _isDataShape2DScan(self, indepShapes, depShapes):
    
    if len(indepShapes)!=2:
      return False
    elif not ((indepShapes[0] == [1] and indepShapes[1] == [2])
           or (indepShapes[0] == [1] and indepShapes[1] == [2])):
      return False
    else:
      for ii in range(0, len(depShapes)):
        if len(depShapes[ii])!=1 or depShapes[ii]<2:
          return False
        elif ii>0 and depShapes[ii] != lastShape:
          return False
        lastShape = depShapes[ii]
    return True
        

  def _isDataArbitraryOption1(self, indepShapes, depShapes, data):
    allShapes = indepShapes+depShapes
    for shape in allShapes:
      if shape != [1]:
        return False
    data = np.asarray(data)
    if len(data.shape)==2 and data.shape[1] == len(allShapes):
      return True
    else:
      return False
    
##  def _isColumnHomogeneousList(self, colVal):
##    tup = None
##    checked = []
##    for value in np.ndenumerate(colVal):
##        tup = value[0][:-1]
##        for ii in range(0, len(tup)):
##          if tup not in checked:
##            checked.append(tup)
##            if not isinstance(self.valByTup(tup, colVal),
##                              (list, np.ndarray)):
##              return False
##            tup = tup[:-1]
##    return True
##
##  def valByTup(self, tupl, array):
##      answer = array
##      for i in tupl:
##          answer = answer[i]
##      return answer


#automatically close file when new one is created or object is killed
#make sure that files are always closed and we dont run into file already open conflicts
##TODO:
    ##cut lines to <=72 characters
    ##add dictionary parameter capabilities ***
    ##over night writes both locally and on afs data corruption tests
    ##add datetime format
    ##refactor
