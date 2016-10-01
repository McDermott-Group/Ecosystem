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

VAR_NAME_INDEX = 0
VAR_SHAPE_INDEX = 1
VAR_TYPE_INDEX = 2
VAR_UNIT_INDEX = 3

EXPECTED_TUPLE_LEN = 4
EXPECTED_TUPLE_TYPES = [str, list, str, str]

ERROR_GRAMMAR = {
    '0':"th",
    '1':"st",
    '2':"nd",
    '3':"rd",
    '4':"th"
}

VALID_DATA_TYPES = ['bool_', 'int8', 'int16', 'int32', 'int64',
                    'uint8', 'uint16', 'uint32', 'uint64',
                    'int_', 'float16', 'float32', 'float64',
                    'float_', 'complex64', 'complex128',
                    'complex_', 'utc_datetime','string'
                    ]

class dataChest(dateStamp):

  def __init__(self, path, setWorkingDirectoryToRoot = False): #add for ability to set root path 
    self.cwdPath = os.environ["DATA_CHEST_ROOT"] #Make sure this exists
    if not setWorkingDirectoryToRoot:
      self._initializeRoot(path)
    self.root = self.cwdPath
    self.dateStamp = dateStamp()
    self.currentHDF5Filename = None
    self.readOnlyFlag = False
    self.varDict = {}
    self.varDict["independents"] = {}
    self.varDict["dependents"] ={}
    self.numIndepWrites = 0
    self.numDepWrites = 0

  def _initializeRoot(self, path):
    if isinstance(path, str):
      if len(path)>0:
        if path not in self.ls()[1]:
          self.mkdir(path)
        self.cd(path)
        self.root = self.cwdPath
      else:
        raise ValueError("Empty strings are invalid root paths.")
    elif isinstance(path, list):
      if len(path)>=1:
        for ii in range(0, len(path)):
          if len(path[ii]) > 0:
            if path[ii] not in self.ls()[1]:
              self.mkdir(path[ii])
            self.cd(path[ii])
            self.root = self.cwdPath
          else:
            raise ValueError(
              "Empty strings are invalid entries in root path lists."
              )
      else:
        raise ValueError("Empty lists are invalid root path lists.")
    else:
      raise TypeError("String and List type paths only.")

  def mkdir(self, directoryToMake):
    """Makes a new directory within the current working directory."""
    dirContents = self.ls()[1]
    if self._formatFilename(directoryToMake, " +-.") == directoryToMake:
      if directoryToMake not in dirContents:
        os.mkdir(self.cwdPath+"/"+directoryToMake) #Try except this even though safe guarded
        return directoryToMake
      else:
        raise ValueError(
          "Directory already exists.\r\n\t"
          + "Directory name provided: "
          + directoryToMake
          )
    else:
      raise ValueError(
        "Invalid directory name provided.\r\n\t"
        + "Directory name provided: "+ directoryToMake+".\r\n\t"
        + "Suggested name: "+ self._formatFilename(directoryToMake, " +-.")
        ) 

  def ls(self):
    """Lists the contents of the current working directory."""
    cwdContents = os.listdir(self.cwdPath)
    files = []
    folders = []
    for item in cwdContents:
      if not item.startswith('.'): #ignore hidden sys files
        if os.path.isfile(os.path.join(self.cwdPath,item)):
          files.append(item)
        elif os.path.isdir(os.path.join(self.cwdPath,item)):
          folders.append(item)
    files = sorted(files) #alphabetize for readibility
    folders = sorted(folders)
    return [files, folders]

  def pwd(self):
    return self.cwdPath

  def cd(self, directoryToMove):
    """Changes the current working directory."""
    if isinstance(directoryToMove, str):
      path = [directoryToMove]
    elif isinstance(directoryToMove, list):
      path = directoryToMove
    else:
      raise TypeError(
        "Acceptable input types are strings e.g.\"SomeFolder\"\r\n\t"
        + "and lists e.g. [\"Folder\",\"subFolder\"]\r\n\t"
        + "corresponding to the path \\Folder\\subFolder."
        )
        
    if len(path)>0:
      for ii in range(0, len(path)):
        cwdContents = self.ls()
        if (path[ii] in cwdContents[1]):
          self.cwdPath = self.cwdPath+"/"+path[ii]
        elif path[ii]=="..":
          lastFolder = self.cwdPath.split("/")[-1]
          self.cwdPath = self.cwdPath[:-(len(lastFolder)+1)]
        elif path[ii]=="":
          self.cwdPath = self.root
        else:
          raise IOError(
            "Directory does not exist.\r\n\t"
            + "Directory name provided: "
            + str(directoryToMove)
            )
      if hasattr(self, 'root') and self.root not in self.cwdPath:
        self.cwdPath = self.root
        raise IOError("cd() cannot be used to take users out of root.")
      return self.cwdPath
    else:
      raise Warning("Calling cd() on an empty list has no meaning.")
    
  def createDataset(self, datasetName, indepVarsList,
                    depVarsList, dateStamp = None):
    "Creates a new dataset within the current working directory."""
    
    self.currentHDF5Filename = None
    self.readOnlyFlag = False
    self.dataCategory = None #treat self.dataCategory consistently
    
    if datasetName != self._formatFilename(datasetName, " +-."):
      raise self.exception
    elif not self._isVarsListValid("independents", indepVarsList): 
      raise self.exception
    elif not self._isVarsListValid("dependents", depVarsList):
      raise self.exception
    elif self._getVariableNames(indepVarsList+depVarsList)==[]:
      raise self.exception
    elif dateStamp is not None:
      RE = re.compile(r'^[a-z]{3}[0-9]{4}[a-z]{3}$')
      if not bool(RE.search(dateStamp)):
        raise IOError("Invalid dateStamp provided.")
    
    filename = self._generateUniqueFilename(datasetName, dateStamp)
    if len(filename)>0:
      self.dataCategory = self._categorizeDataset(self.varDict)
      self._initDataset(self.varDict, filename)
    else:
      raise RuntimeError("Unable to create a unique filename.")

  def getDatasetName(self):
    if self.currentHDF5Filename is not None:
      self._updateFileDate("Date Accessed")
      return self.currentHDF5Filename.split("/")[-1]
    else:
      raise Warning("No dataset is currently open.")

  def getVariables(self):
    if self.currentHDF5Filename is not None:
      indeps = self._varListFromGrp(self.file["independents"])
      deps = self._varListFromGrp(self.file["dependents"])
      self._updateFileDate("Date Accessed")
      return [indeps, deps]
    else:
      raise Warning(
        "No file is currently selected. First select a file\r\n\t"
        + "using openDataset() to open an existing set or\r\n\t"
        + "create one using createDataset()."
        )

  def addData(self, data):
    """Adds data to the latest dataset created with new."""
    
    if self.readOnlyFlag == True: 
      raise Warning(
        "You cannot gain write privileges to this file as it was\r\n\t"
        + "opened read-only. Datasets opened with openDataset()\r\n\t"
        + "are read-only by default. You must set the optional\r\n\t"
        + "argument modify = True in the openDataset() method\r\n\t"
        + "or create a new dataset with createDataset() before\r\n\t"
        + "using addData()."
        )
    elif self.currentHDF5Filename is not None:
      if self._isDataValid(data):
        numIndeps = len(self.varDict["independents"]["names"])
        numDeps = len(self.varDict["dependents"]["names"])
        numRows = len(data)
        indepShapes = self.varDict["independents"]["shapes"]
        depShapes = self.varDict["dependents"]["shapes"]
        if self.dataCategory == "Arbitrary Type 1":
          for colNum in range(0, numIndeps+numDeps):
            column = [data[ii][colNum] for ii in range(0, len(data))]
            column = np.asarray(column)
            if colNum<numIndeps:
              varGrp = "independents"
              varName = self.varDict[varGrp]["names"][colNum]
              flatLen = len(column)
              self._addToDataset(self.file[varGrp][varName],
                                 column,
                                 flatLen,
                                 self.numIndepWrites)
            else:
              varGrp = "dependents"
              varName = self.varDict[varGrp]["names"][colNum-numIndeps]
              flatLen = len(column)
              self._addToDataset(self.file[varGrp][varName],
                                 column,
                                 flatLen,
                                 self.numDepWrites)
          self.numIndepWrites = self.numIndepWrites+flatLen
          self.numDepWrites = self.numDepWrites+flatLen
        else:
          for rowIndex in range(0, numRows):
            for colNum in range(0, len(data[rowIndex])):
              if colNum<numIndeps:
                varGrp = "independents"
                varName = self.varDict[varGrp]["names"][colNum]
                varData = np.asarray(data[rowIndex][colNum])
                varShapes = self.varDict[varGrp]["shapes"]
                flatLen = self._flatShape(varShapes[colNum])[0]
                self._addToDataset(self.file[varGrp][varName],
                                   varData,
                                   flatLen,
                                   self.numIndepWrites)
              else:
                varGrp = "dependents"
                varName = self.varDict[varGrp]["names"][colNum-numIndeps]
                varData = np.asarray(data[rowIndex][colNum])
                varShapes = self.varDict[varGrp]["shapes"]
                flatLen = self._flatShape(varShapes[colNum-numIndeps])[0]
                self._addToDataset(self.file[varGrp][varName],
                                   varData,
                                   flatLen,
                                   self.numDepWrites)
                
            self.numIndepWrites = self.numIndepWrites + 1
            self.numDepWrites = self.numDepWrites + 1
            
        self.file.attrs["Number Of Rows Added"] = self.numIndepWrites
        self.file.flush()
      else:
        raise self.exception
    else:
      raise Warning(
        "You must create a dataset before attempting to write.\r\n\t"
        + "Datasets are created using the createDataset().\r\n\t"
        )
    
    dateISO = self.dateStamp.utcDateIsoString()
    self._updateFileDate("Date Accessed", dateISO)
    self._updateFileDate("Date Modified", dateISO)
    return True

  def getNumRows(self):
    if self.currentHDF5Filename is not None:
      self._updateFileDate("Date Accessed")
      return self.file.attrs["Number Of Rows Added"]
    else:
      raise Warning("No dataset is currently open.")

  def getData(self, startIndex = np.nan, stopIndex = np.nan):
    """Retrieves data from the current dataset."""
    if self.currentHDF5Filename is not None:
      dataDict = {}
      numRows = self.file.attrs["Number Of Rows Added"]
      sliceIndices = self._sortSliceIndices(startIndex, stopIndex, numRows)
      if not isinstance(sliceIndices, list):
        raise self.exception
      startIndex, stopIndex = sliceIndices[0], sliceIndices[1]

      for varTypes in self.varDict.keys():
        for variables in self.file[varTypes].keys():
          varGrp = self.file[varTypes]
          dataset = varGrp[variables].value
          originalShape = varGrp[variables].attrs["shapes"]
          chunkSize = self._flatShape(originalShape)[0]
          totalLen = varGrp[variables].shape[0]
          numChunks = totalLen/chunkSize
          dataDict[variables]=[]
          if len(originalShape)>1 or originalShape!=[1]:           
            for ii in range(0, numRows):
              chunk = np.asarray(dataset[ii*chunkSize:(ii+1)*chunkSize])
              chunk = np.reshape(chunk, tuple(originalShape))
              dataDict[variables].append(chunk.tolist())
          else:
            if len(dataset) != numRows:
              dataset = dataset[0:numRows]
            dataDict[variables] = dataset

      data = []
      allVars = (self.varDict["independents"]["names"]
                 + self.varDict["dependents"]["names"])
      if self.getDataCategory() == "Arbitrary Type 1":
        for ii in range(0, len(allVars)):
          data.append(dataDict[allVars[ii]])
        data = np.asarray(data)
        data = data.T
        self._updateFileDate("Date Accessed")
        return data[startIndex:stopIndex]
      else:
        for ii in range(startIndex,stopIndex): #making slicing efficient
          row = []
          for jj in range(0,len(allVars)):
            row.append(dataDict[allVars[jj]][ii])
          data.append(row)
        self._updateFileDate("Date Accessed")
        return data
    else:
      raise Warning(
        "No file is currently open. First select a file using\r\n\t"
        + "either openDataset() to open an existing set or with\r\n\t"
        + "createDataset()."
        )

  def openDataset(self, filename, modify = None):
    """Opens a dataset in the current working directory if it exists."""
    if '.hdf5' not in filename: #adds file extension if omitted
      filename = filename+".hdf5"
    existingFiles = self.ls()[0]
    if filename in existingFiles:
      if hasattr(self, 'currentFile'):
        self.file.close() #close current file if existent
      self.file = h5py.File(self.pwd()+"/"+filename,'r+') #read+write
      self.currentHDF5Filename = self.pwd() + "/" + filename
      if modify is True:
        self.readOnlyFlag = False
      else:
        self.readOnlyFlag = True
      self._updateFileDate("Date Accessed")
  
      for varType in self.varDict.keys(): #copying varDict from file
        varGroupAttributes = self.file[varType].attrs.keys()
        varGrp = self.file[varType]
        for item in varGroupAttributes:
          self.varDict[varType][str(item)] = varGrp.attrs[item].tolist()

      self.dataCategory = self.file.attrs["Data Category"]
      self.numIndepWrites = self.file.attrs["Number Of Rows Added"]
      self.numDepWrites = self.numIndepWrites    
    else:
      self.currentHDF5Filename = None
      raise Warning(
        "File not found, please cd into the directory with\r\n\t"
        + "the desired dataset."
        )

  def addParameter(self, paramName, paramValue, overwrite = None): 
    if self.readOnlyFlag == True:
      raise Warning(
        "You cannot add parameters to this file as it was\r\n\t"
        + "opened read only. Files opened with openDataset()\r\n\t"
        + "are read only by design. You must make a new set\r\n\t"
        + "if you wish to add parameters to one."
        )
    elif self.currentHDF5Filename is not None:
      if self._isParameterValid(paramName, paramValue, overwrite):
        dateISO = self.dateStamp.utcDateIsoString()
        self._updateFileDate("Date Accessed", dateISO)
        self._updateFileDate("Date Modified", dateISO)
  
        self.file["parameters"].attrs[paramName] = paramValue
        self.file.flush()
      else:
        raise self.exception
    else:
      raise Warning(
        "No file is currently selected. Create a file using\r\n\t"
        + "createDataset() before using addParameter()."
        )
      
  def getParameter(self, parameterName, byIOError=False):
    if self.currentHDF5Filename is not None:
      if parameterName in self.file["parameters"].attrs.keys():
        self._updateFileDate("Date Accessed")
        return self.file["parameters"].attrs[parameterName]
      else:
        if not byIOError:
          raise IOError("Parameter name not found.")
        else:
          return None
    else:
      raise Warning(
        "No file is currently selected. First select a file\r\n\t"
        + "using either openDataset() to open an existing set\r\n\t"
        + "or with createDataset()."
        )

  def getDataCategory(self):
    if self.currentHDF5Filename is not None:
        self._updateFileDate("Date Accessed")
        return self.file.attrs["Data Category"]
    else:
      raise Warning(
        "No file is currently selected. First select a file\r\n\t"
        + "select a file using either openDataset() to open an\r\n\t"
        + "existing set or with createDataset()."
        )

  def getParameterList(self):
    if self.currentHDF5Filename is not None:
      unicodeList = self.file["parameters"].attrs.keys()
      self._updateFileDate("Date Accessed")
      return [str(x) for x in unicodeList]
    else:
      raise Warning(
        "No file is currently selected. Please select a file\r\n\t"
        + "using either openDataset() to open an existing set or\r\n\t"
        + "with createDataset()."
        )
    
  def _updateFileDate(self, dateCategory, dateISO = None):
    if self.currentHDF5Filename is not None:
      if dateCategory in ["Date Created", "Date Modified", "Date Accessed"]:
        if dateISO is None:
          self.file.attrs[dateCategory] = self.dateStamp.utcDateIsoString()
        else:
          self.file.attrs[dateCategory] = dateISO
      else:
        raise ValueError("Invalid dateCategory provided.")

    else:
      raise IOError(
        "Attempted to update metadata for a file that does not exist."
        )
    

  def _initDataset(self, varDict, filename):

    self.numIndepWrites = 0
    self.numDepWrites = 0
    
    self.file = h5py.File(self.pwd()+"/"+filename) #Try catch this
    self.currentHDF5Filename = self.pwd()+"/"+filename
    self.readOnlyFlag = False # gives user read and write access
    
    #create base groups within new file
    self.file.create_group("independents")
    self.file.create_group("dependents")
    self.file.create_group("parameters")

    self.file.attrs["Data Category"] = self.dataCategory
    self.file.attrs["Number Of Rows Added"] = 0
    dateISO = self.dateStamp.invertDateStamp(filename.split("_")[0])
    #date = self.dateStamp.invertDateStamp(filename.split("_")[0])
    self._updateFileDate("Date Created", dateISO)
    self._updateFileDate("Date Modified", dateISO)
    self._updateFileDate("Date Accessed", dateISO)
    

    #varTypes in ['independents', 'dependents']
    #varAttrs in ['shapes','units','names','types']
    for varTypes in varDict.keys():
      for varAttrs in varDict[varTypes].keys():
        varGrp = self.file[varTypes]
        varGrp.attrs[varAttrs] = varDict[varTypes][varAttrs]
      self._initDatasetGroup(varGrp, varDict[varTypes])
    self.file.flush()
    
  def _initDatasetGroup(self, group, varDict):
    
    for ii in range(0, len(varDict["names"])):
      #creates a datatype, chunksize, maxshape, fillvalue for each var
      varType = varDict["types"][ii]
      if varType == 'string':
        dataType = h5py.special_dtype(vlen=str)
        dShape = tuple(self._flatShape(varDict["shapes"][ii]))
        dset = group.create_dataset(varDict["names"][ii],
                                    dShape,
                                    dtype=dataType,
                                    chunks=dShape,
                                    maxshape=(None,))       
      else:
        if varType == 'utc_datetime':
          dataType = 'float64'
        else:
          dataType = varDict["types"][ii]
        fillVal = None
        dShape = tuple(self._flatShape(varDict["shapes"][ii]))
        if dShape == (1,):
          chunkShape = (10000,)
        else:
          chunkShape = dShape
        dset = group.create_dataset(varDict["names"][ii],
                                    dShape,
                                    dtype=dataType,
                                    chunks=chunkShape,
                                    maxshape=(None,),
                                    fillvalue=fillVal)
  
      #stores name, shape, type, and units as attributes for this dset
      #(sort of redundant as this is done at the varType group level)?
      for keys in varDict:
        if isinstance(varDict[keys][ii], str):
          dset.attrs[keys] = unicode(varDict[keys][ii], "utf-8")
        elif isinstance(varDict[keys][ii], list):
          dset.attrs[keys] = varDict[keys][ii]
        else:
          raise TypeError(
            "Unrecognized dtype receieved.\r\n\t"+
            "Type: "+str(type(varDict[keys][ii]))
            )

  def _generateUniqueFilename(self, datasetName, dateStamp):
    uniquenessFlag = False
    uniqueName = ""
    maxTries = 100
    ii = 0
    existingNames = self.ls()[0]
    while ii<maxTries and uniquenessFlag == False:
      if dateStamp is None:
        fileDateStamp = self.dateStamp.dateStamp()
      else:
        fileDateStamp = dateStamp
      if ii == 0:
        uniqueName = (fileDateStamp +
                      "_"+datasetName+".hdf5")
      else:
        uniqueName = (fileDateStamp +
                      "_"+str(ii)+"_"+datasetName+".hdf5") 

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

  def _varListFromGrp(self, varDict):
    names = varDict.attrs["names"]
    shapes = varDict.attrs["shapes"]
    types = varDict.attrs["types"]
    units = varDict.attrs["units"]
    varList = []
    for ii in range(0, len(names)):
      varTup = (names[ii],shapes[ii].tolist(),types[ii],units[ii])
      varList.append(varTup)
    return varList
    
  def _formatFilename(self, fileName, additionalChars=None): 
      """Returns a valid filename from the filename provided."""
      defaultCharsTup = (string.ascii_letters, string.digits)
      if isinstance(fileName, str):
        if len(fileName)==0:
          self.exception = TypeError("Filenames cannot be empty.")
          return "Error" #fix this          
        elif additionalChars is None:
          validChars = "_%s%s" % defaultCharsTup
        else:
          validChars = "_"+additionalChars
          validChars = validChars+"%s%s" % defaultCharsTup
        tempFilename = ''.join(c for c in fileName if c in validChars)
        if fileName == tempFilename:
          return fileName
        else:
          self.exception = ValueError(
            "Invalid characters were detected in your filename."
            )
          return tempFilename
      else:
        self.exception = TypeError("Filenames should be type str.")
        return ""

  def _sortSliceIndices(self, startIndex, stopIndex, numRows):

    if startIndex is None: #make sure types are correct int, np.nan. or None
      startIndex = 0
    if stopIndex is None:
      stopIndex = numRows
    if startIndex !=0 and startIndex/abs(startIndex) == -1:
      startIndex = abs(startIndex)
      if startIndex >= numRows:
        if startIndex > numRows and stopIndex is np.nan:
          self.exception = IndexError("startIndex is out of range.")
          return "Error"
        else:
          startIndex = 0
      else:
        startIndex = numRows-startIndex
    if stopIndex !=0 and stopIndex/abs(stopIndex) == -1:
      stopIndex = abs(stopIndex)
      if stopIndex >= numRows:
        if startIndex is np.nan:
          self.exception = IndexError(
            "startIndex should be provided when attempting\r\n\t"
            + "to obtain a single row."
            )
          return "Error"
        else:
          stopIndex = 0
      else:
        stopIndex = numRows-stopIndex
        
    if startIndex >= numRows:
      if stopIndex is not np.nan: #intent to slice
        startIndex = numRows
      else:
        self.exception = IndexError("startIndex is out of range.")
        return "Error"
      
    if stopIndex > numRows:
      if startIndex is not np.nan: #intent to slice
        stopIndex = numRows
      else:
        self.exception = IndexError(
          "startIndex should be provided when attempting\r\n\t"
          + "to obtain a single row."
          )
        return "Error"
    if [startIndex, stopIndex] == [np.nan, np.nan]:
      startIndex = 0
      stopIndex = numRows
    elif stopIndex is np.nan:
      stopIndex = startIndex + 1
    return [startIndex, stopIndex]

  def _areTypesValid(self, dtypes):
    for ii in range(0, len(dtypes)):
      if dtypes[ii] not in VALID_DATA_TYPES:
        self.exception = ValueError(
          "An invalid datatype was detected.\r\n\t"
          + "Type provided="+str(dtypes[ii])+"\r\n\t"
          + "Valid types="+str(VALID_DATA_TYPES)
          )
        return False
    return True
          
  def _getVariableNames(self, varsList):
    varNames = []
    for ii in range(0, len(varsList)):
      varName = varsList[ii][VAR_NAME_INDEX]
      if self._formatFilename(varName, " +-.") == varName:
        varNames.append(varName)
      else:
        self.exception = ValueError(
          "Invalid variable name provided.\r\n\t"
          + "Name provided: "+varName+
          + ".\r\n\t"+"Suggested alternative: "
          + self._formatFilename(varName, " +-.")
          )
        return []
    if len(varNames) != len(set(varNames)):
      self.exception = ValueError("Variable names must be distinct.")
      varNames = []                    
    return varNames

  def _getVariableShapes(self, varsList):
    varShapes= []
    for ii in range(0, len(varsList)):
      if len(varsList[ii][VAR_SHAPE_INDEX])>0:
        for kk in range(0, len(varsList[ii][VAR_SHAPE_INDEX])):
          if not isinstance(varsList[ii][VAR_SHAPE_INDEX][kk], int):
            self.exception = TypeError(
              "Non integer shapes are forbidden."
              )
            return []
          elif varsList[ii][VAR_SHAPE_INDEX][kk]<=0:
            self.exception = ValueError(
              "Non integer shapes are forbidden."
              )
            return []
      else:
        self.exception = ValueError(
          "Shapes cannot be the empty lists."
          )
      varShapes.append(varsList[ii][VAR_SHAPE_INDEX])
    return varShapes

  def _getVariableTypes(self, varsList):
    varTypes= []
    for ii in range(0, len(varsList)):
      varTypes.append(varsList[ii][VAR_TYPE_INDEX])
    if not self._areTypesValid(varTypes):
      varTypes = []
    return varTypes

  def _getVariableUnits(self, varsList): #***ADD UNITS CHECK
    varTypes= []
    for ii in range(0, len(varsList)):
      varTypes.append(varsList[ii][VAR_UNIT_INDEX])
    return varTypes

  def _addToDataset(self, dset, data, chunkSize, numWrites):
    if numWrites == 0:
      data = np.reshape(data, (chunkSize,))
      if dset.shape[0] == 1 and len(dset.shape) == 1: #arbitrary type 1 hack
        dset.resize((chunkSize,))
      dset[:chunkSize] = data
    else:
      data = np.reshape(data, (chunkSize,))
      dset.resize((dset.shape[0]+chunkSize,))
      dset[-chunkSize:] = data

  def _isDataValid(self, data):
    if isinstance(data, (list, np.ndarray)): # checks that its a list
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
            if not ((isinstance(data[ii], list) or
                     isinstance(data[ii], np.ndarray))):
              self.exception = TypeError(
                "For row ="+str(ii)
                + " of the data entered is not a list.\r\n\t"
                + "Data entered should be of the form: \r\n\t"
                + "[[indep1_0, indep2_0, dep1_0, dep2_0], ... \r\n\t"
                + "[indep1_n, indep2_n, dep1_n, dep2_n]] \r\n\t"
                + "where [indep1_m, indep2_m, dep1_m, dep2_m] \r\n\t"
                + "is the m'th row of your data set."
                )
              return False
            else:
              if not self._isRowValid(data[ii]):
                return False
      else: # [] is not a valid dataset
        self.exception = ValueError(
          "Vacuous datasets are invalid."
          )
        return False
    else:
      self.exception = TypeError(
        "The dataset provided was not of type list."
        )
      return False
    return True

  def _isRowValid(self, dataList):
    numIndeps = len(self.varDict["independents"]["names"])
    numDeps = len(self.varDict["dependents"]["names"])
    if len(dataList) == (numIndeps+numDeps):
      for ii in range(0, (numIndeps+numDeps)):
##        if self._isColumnHomogeneousList(dataList[ii]):#subelements
        array = np.asarray(dataList[ii])        
        if ii < numIndeps:
          varShape = self.varDict["independents"]["shapes"][ii]
          varType = self.varDict["independents"]["types"][ii]
          if varShape==[1]:
            if array.shape!=():
              self.exception = TypeError(
                "Data with shape = [1] should not be placed\r\n\t"
                + "within a list."
                )
              return False
          elif array.shape != tuple(varShape):
            self.exception = ValueError(
              "Data shapes do not match for the independent"
              + "variable data.\r\n\t"
              + "Expected shape: "
              + str(tuple(varShape))+".\r\n\t"
              + "Shape received: "+str(array.shape)
              )
            return False
          elif varType == 'string':
            if not self._isArrayAllStrings(array):
              self.exception = TypeError(
                "Expecting string data."
                )
              return False
          elif varType == 'utc_datetime':
            if array.dtype.name!="float64":
              self.exception = TypeError(
                "utc_datetime data should be a float64."
                )
              return False
            
          elif array.dtype.name != varType:
            self.exception = TypeError(
              "Types do not match for independents"
              )
            return False           
        else:
          varShape = self.varDict["dependents"]["shapes"][ii-numIndeps]
          varType = self.varDict["dependents"]["types"][ii-numIndeps]
          if varShape==[1]:
            if array.shape!=():
              self.exception = TypeError(
                "Date with shape = [1] should\r\n\t"
                + "not be placed within a list."
                )
              return False
          elif array.shape != tuple(varShape):
            self.exception = ValueError(
              "Data shapes do not match for "
              + "the dependent variable data.\r\n\t"
              + "Expected shape: "
              + str(tuple(varShape))+".\r\n\t"
              + "Received shape: "
              + str(array.shape)
              )
            return False
          elif varType == 'string':
            if not self._isArrayAllStrings(array):
              self.exception = TypeError(
                "Expecting string data."
                )
              return False
          elif varType == 'utc_datetime':
            if array.dtype.name!="float64":
              self.exception = TypeError(
                "utc_datetime data should be a float64."
                )
              return False
            
          elif array.dtype.name != varType:
            self.exception = TypeError(
              "Types do not match for dependents."
              )
            return False
##        else:
##          self._dataChestError("The column elements (along with all subelements)\r\n\t"+
##                               "of a row must be of type list or a numpy ndarray.")
##          return False
    else:
      self.exception = ValueError(
        "Incorrect number of data columns provided."
        )
      return False
    return True

  def _flatShape(self, shapeList):
    totalDim = 1
    for ii in range(0, len(shapeList)):
      totalDim = totalDim*shapeList[ii]
    return [totalDim]
      
  def _isVarsListValid(self, varCategory, varsList): #nonlocal
    if isinstance(varsList, list):
      if len(varsList) == 0:
        self.exception = ValueError(
          "A data set with no "
          + varCategory
          + " has no meaning.")
        return False
      for ii in range(0, len(varsList)): #validity of each dep/indep tup
        if not self._isTupleValid(varCategory, varsList[ii]):
          return False
      self._updateVariableDict(self.varDict[varCategory], varsList)
      for varAttributes in self.varDict[varCategory].keys():
        if len(self.varDict[varCategory][varAttributes])==0:
          return False
      return True
    else:
      self.exception = TypeError(
        "Expecting list of "+varCategory+" variables."
        )     
      return False

  def _isTupleValid(self, varType, tupleValue): #local
    
    if not isinstance(tupleValue, tuple): #is it a tuple
      self.exception = TypeError(
        "Expecting list elements to be tuples"
        ) 
      return False
    elif not(len(tupleValue) == EXPECTED_TUPLE_LEN): #expected length
      self.exception = ValueError(
        "Expecting tuple elements to be of length "
        + str(EXPECTED_TUPLE_LEN)
        )      
      return False
    
    for jj in range(0, len(EXPECTED_TUPLE_TYPES)):#Loops over elements
      if not isinstance(tupleValue[jj], EXPECTED_TUPLE_TYPES[jj]):#types
        self.exception = TypeError(
          "In the "+varType
          + " variables list,\r\n\t"
          + "for the tuple ="
          + str(tupleValue)
          + ",\r\n\t"
          + "the "+str(jj)+ERROR_GRAMMAR[str(jj)]
          + " element should be of\r\n\t"
          + str(EXPECTED_TUPLE_TYPES[jj])
          )
        return False
    return True

  def _isParameterValid(self, parameterName, parameterValue, overwrite = None):

    validTypes = (int, long, float, complex, bool,
                  list, np.ndarray, str, unicode)
    if isinstance(parameterName, str):
      if self._formatFilename(parameterName, " +-.") != parameterName:
        self.exception = ValueError("Invalid parameter name provided.")
        return False
      elif not isinstance(parameterValue, validTypes): 
        self.exception = ValueError(
          "Invalid datatype parameter\r\n\t"
          + "was provided.\r\n\t"
          + "Accepted types: int, long, float,\r\n\t"
          + "complex, bool, list, np.ndarray,\r\n\t"
          + "str, unicode.\r\n\t"
          + "Type provided=", type(parameterValue)
          )
        #lists must be of one type or else type conversion occurs
        #[12.0, 5e-67, "stringy"] --> ['12.0', '5e-67', 'stringy']
        return False
      elif overwrite is None and parameterName in self.file["parameters"].attrs.keys():
        self.exception = RuntimeError(
          "Parameter name already exists. \r\n\t"
          +"Parameter values cannot be overwritten."
          )
        return False
      else:
        return True
    else:
      self.exception = TypeError(
        "Parameter names must be of type str."
        )
      return False

  def _isStringUTCFormat(self, dateStr):
    RE = re.compile(r'^\d{4}-\d{2}-\d{2}[T]\d{2}:\d{2}:\d{2}[.]\d{6}$')
    return bool(RE.search(dateStr))

  def _categorizeDataset(self, varDict): #local
    
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

  def _isDataShapeArbType1(self, indepShapes, depShapes): #local
    allShapes = indepShapes+depShapes
    for shape in allShapes:
      if shape != [1]:
        return False
    return True

  def _isDataFormatArbType1(self, data, varDict): #need to check that lengths are correct**** catch data = [x,y] case
    indepShapes = varDict["independents"]["shapes"]
    depShapes = varDict["dependents"]["shapes"]

    indepTypes = varDict["independents"]["types"]
    depTypes = varDict["dependents"]["types"]
    types = indepTypes + depTypes
    
    dataShape = np.asarray(data).shape

    totalNumVars = len(indepShapes+depShapes)
    if len(dataShape) != 2:
      self.exception = ValueError(
        "Arbitrary Type 1 Data has rows\r\n\t"
        + "of the form:\r\n\t"
        + "[indep1,...,indepM,dep1,...,depN]\r\n\t"
        + "where each column entry is a\r\n\t"
        + "scalar. The data is then a list of\r\n\t"
        + "rows i.e. data = [row1,row2,...,rowK]."
        )
      return False
    elif dataShape[1] != totalNumVars:
      self.exception = ValueError(
        "Invalid number of columns provided.\r\n\t"
        + "Arbitrary Type 1 Data has rows\r\n\t"
        + "of the form:\r\n\t"
        + "[indep1,...,indepM,dep1,...,depN]\r\n\t"
        + "where each column entry is a\r\n\t"
        + "scalar. Each row should have M+N columns\r\n\t"
        )
      return False
    #transposedData = data.T
    for colIndex in range(0, totalNumVars):
        #column = transposedData[colIndex]
        column = [data[ii][colIndex] for ii in range(0, len(data))]
        #column = data[:,colIndex]
        column = np.asarray(column)
        columnShape = column.shape
        dtype = column.dtype.name
        if len(columnShape)!=1:
          self.exception = ValueError(
            "Data with shape = [1] should\r\n\t"
            + "be entered into columns as number\r\n\t"
            + "e.g. -11.756 and not [-11.756]"
            )
          return False
        elif types[colIndex] == 'string':
          if not self._isArrayAllStrings(column):
            self.exception = TypeError(
              "Expected all entries of this\r\n\t"
              + "particular column to be of type string."
              )
            return False
        elif types[colIndex] == 'utc_datetime':
          if dtype != 'float64':
            self.exception = TypeError(
              "utc_datetime data should be a float64."
              )
            return False
        elif dtype != types[colIndex]:
          self.exception = TypeError(
            "Expected all entries of this\r\n\t"
            + "particular column to be of type:\r\n\t"
            + types[colIndex]+"\r\n\t"
            + "Instead received data of type:\r\n\t"
            + dtype
            )
          return False
        elif colIndex>2 and columnShape != lastShape:
            self.exception = TypeError(
              "Arbitrary 1D Data requires one value\r\n\t"
              + "for each independent and dependent\r\n\t"
              + "variable per row of data."
              )
            return False
        lastShape = column.shape
    return True

  def _isArrayAllStrings(self, array):
    for ii in range(0, len(array)):
      if not isinstance(array[ii], str):
        return False
    return True

  def _isDataFormatArbType2(self, data, varDict): #need to check that lengths are correct****, catch data = [x,y] case
    indepShapes = varDict["independents"]["shapes"]
    depShapes = varDict["dependents"]["shapes"]
    allShapes = indepShapes+depShapes

    indepTypes = varDict["independents"]["types"]
    depTypes = varDict["dependents"]["types"]
    types = indepTypes + depTypes
    
    dataShape = np.asarray(data).shape
    totalNumVars = len(indepShapes+depShapes)
    if len(dataShape) != 3:  # (1,totalNumVars,lengthOfDataArray)
      self.exception = ValueError(
        "Arbitrary Type 2 Data has rows\r\n\t"
        + "of the form:\r\n\t"
        + "[indep1,...,indepM,dep1,...,depN]\r\n\t"
        + "where each column entry is a\r\n\t"
        + "1D array (same length for all columns).\r\n\t"
        + "The data is then a list of\r\n\t"
        + "rows i.e. data = [row1,row2,...,rowK]."
        )
      return False
    elif dataShape[1] != totalNumVars:
      self.exception = ValueError(
        "Invalid number of columns provided.\r\n\t"
        + "Arbitrary Type 1 Data has rows\r\n\t"
        + "of the form:\r\n\t"
        + "[indep1,...,indepM,dep1,...,depN]\r\n\t"
        + "where each column entry is a\r\n\t"
        + "1D array (same length for all columns).\r\n\t"
        + "Each row should have M+N columns."
        )
      return False
    elif dataShape[2] < 2: #==> option 1 or mishapen (investigate mishapen aspect)
      self.exception = ValueError(
        "Arbitrary Type 2 Data column\r\n\t"
        + "elements should all be of length > 2."
        )
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
              self.exception = TypeError(
                "Expected all entries of this\r\n\t"
                + "particular column to be of type string."
                )
              return False
          elif types[colIndex] == 'utc_datetime':
            if dtype != 'float64':
              self.exception = TypeError(
                "utc_datetime data should be a float64."
                )
              return False
          elif dtype != types[colIndex]:
            self.exception = TypeError(
              "Expected all entries of this\r\n\t"
              + "particular column to be of type:\r\n\t"
              + types[colIndex]
              + "\r\n\t"
              + "Instead received data of type:\r\n\t"
              + dtype
              )
            return False
          elif columnShape != tuple(allShapes[colIndex]):
            self.exception = ValueError(
              "Column entry has incorrect size\r\n\t"
              + "or shape.\r\n\t"
              + "Received a "+str(len(columnShape))
              + "D\r\n\t"
              + "of length "
              + str(columnShape[0])
              + "\r\n\t."
              + "Expecting a 1D array of length: "
              + str(allShapes[colIndex][0])
              )
            
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
    if len(dataShape) != 2:  # (numRows,totalNumVars)
      self.exception = ValueError(
        "1D Scan Data has rows\r\n\t"
        + "of the form:\r\n\t"
        + "[indep1,dep1,...,depN]\r\n\t"
        + "where indep1 is a 1D array of the form\r\n\t"
        + "indep1 = [t_start, t_stop]\r\n\t"
        + "and the dependent entries are 1D arrays\r\n\t"
        + "(all of same length) where we assume\r\n\t"
        + "dep1 = [dep1(t_start),...,dep1(t_stop)]."
        )
      return False
    elif dataShape[1] != totalNumVars:
      self.exception = ValueError(
        "Invalid number of columns provided.\r\n\t"
        + "1D Scan Data has rows\r\n\t"
        + "of the form:\r\n\t"
        + "[indep1,dep1,...,depN]\r\n\t"
        + "where indep1 is a 1D array of the form\r\n\t"
        + "indep1 = [t_start, t_stop]\r\n\t"
        + "and the dependent entries are 1D arrays\r\n\t"
        + "(all of same length). Each row should\r\n\t"
        + "have 1+N columns."
        )
      return False
    
    numRows = dataShape[0]
    numColumns = dataShape[1]
    for rowIndex in range(0, numRows):
      for colIndex in range(0, numColumns):
          column = data[rowIndex][colIndex]
          column = np.asarray(column) #fails to be casted [1.0, [2.0]]
          colShape = column.shape
          dtype = column.dtype.name
          if colIndex == 0 and colShape != (2,):
            self.exception = ValueError(
              "For 1D Scan Data, the first\r\n\t"
              + "entry should be an array of\r\n\t"
              + "the form [t_start, t_stop]\r\n\t"
              )
            
            return False
          elif types[colIndex] == 'string':
            if not self._isArrayAllStrings(column):
              self.exception = TypeError(
                "Expected all entries of this\r\n\t"
                +"particular column to be of type string."
                )
              return False
          elif types[colIndex] == 'utc_datetime':
            if dtype != 'float64':
              self.exception = TypeError(
                "utc_datetime data should be a float64."
                )
              return False
          elif dtype != types[colIndex]:
            self.exception = TypeError(
              "Expected all entries of this\r\n\t"
              + "particular column to be of type:\r\n\t"
              + types[colIndex]
              + "\r\n\t"
              + "Instead received data of type:\r\n\t"
              + dtype
              )
            return False
          elif (colIndex>1 and
                (len(colShape)!=1 or colShape[0]!=shapes[colIndex][0])):
            self.exception = ValueError(
              "Column entry has incorrect size\r\n\t"
              + "or shape.\r\n\t"
              + "Received a "+str(len(colShape))+"D\r\n\t"
              + "of length "+str(colShape[0])
              + "\r\n\t."
              + "Expecting a 1D array of length"
              + str(shapes[colIndex][0])
              )
            return False
      return True

  def _isDataFormat2DScan(self, data, varDict):
    indepShapes = varDict["independents"]["shapes"]
    depShapes = varDict["dependents"]["shapes"]
    shapes = indepShapes + depShapes

    indepTypes = varDict["independents"]["types"]
    depTypes = varDict["dependents"]["types"]
    types = indepTypes + depTypes
    
    totalNumVars = len(shapes)
    numRows = len(data)

    for rowIndex in range(0, numRows):
      row = data[rowIndex]
      col1 = np.asarray(row[0])
      col2 = np.asarray(row[1])
      if len(row) != totalNumVars:
        self.exception = ValueError(
          "Invalid number columns provided."
          )
        return False
      if not (((col1.shape==() and col2.shape==(2,)) or
               (col1.shape==(2,) and col2.shape==()))):
        self.exception = ValueError(
          "Invalid data shape for 2D Scan."
          )
        return False        
      for colIndex in range(0, totalNumVars):
        if colIndex > 1:
          column =np.asarray(row[colIndex])
          columnShape = column.shape
          if (len(columnShape)!=1 or
              column.shape[0]!=shapes[colIndex][0]):
            self.exception = ValueError(
              "Column shape mismatch."
              )
            return False
          elif types[colIndex] == 'string':
            if not self._isArrayAllStrings(column):
              self.exception = TypeError(
                "Expected all entries of this\r\n\t"
                + "particular column to be of type string."
                )
              return False
          elif types[colIndex] == 'utc_datetime':
            if np.asarray(row[colIndex]).dtype.name != 'float64':
              self.exception = TypeError(
                "utc_datetime data should be a float64."
                )
              return False            
          elif np.asarray(row[colIndex]).dtype.name != types[colIndex]:
            self.exception = TypeError(
              "Expected all entries of this\r\n\t"
              + "particular column to be of type:\r\n\t"
              + types[colIndex]
              + "\r\n\t"
              + "Instead received data of type:\r\n\t"
              + dtype
              )
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
    ##refactor

 
