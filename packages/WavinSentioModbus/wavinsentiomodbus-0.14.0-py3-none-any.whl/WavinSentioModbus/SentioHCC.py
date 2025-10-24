import logging

from .SentioRegisterMap import *
from .ModbusWrapper import ModbusWrapper
from .SentioTypes import *
from .Defaults import Defaults

class SentioHccHandler:
    def __init__(self, api:ModbusWrapper):
        self._detectedHccs = []
        self._api = api
        pass

    def initialize(self):
        self._detectedHccs=[]
        for hccCtr in range(Defaults.MaxNumberOfHCCs):
            try:
                value = self._api.readRegister(SentioRegisterMap.HCCControllers.Name, _subIndex = hccCtr)
                if value != None:
                    self._detectedHccs.append(SentioHccCircuit(hccCtr, value, self._api, SentioRegisterMap.HCCControllers))
            except Exception as e:
                logging.exception("Exception reading HCC Circuit {0}".format(e))
                return -1

        return 0
    
    def updateData(self):
        for hcc in self._detectedHccs:
            hcc.updateData()

class SentioHccCircuit:
    def __init__(self, index, name, api:ModbusWrapper, register_handler):
        self.index = index;
        self.name = name;
        self._state         = None
        self._pumpState     = None
        self._inletMeasured = None
        self._inletDesired  = None
        self._returnTemp    = None
        self._supplierTemp  = None
        self._api = api
        self._register_handler = register_handler

    def GetIndex(self):
        return self.index
    
    @property
    def getPumpState(self) -> PumpState:
        return self._pumpState
    
    @property
    def getInletMeasured(self) -> float:
        return self._inletMeasured
        
    @property
    def getInletDesired(self) -> float:
        return self._inletDesired
    @property
    def getSupplierTemp(self) -> float:
        return self._supplierTemp
    
    @property
    def getReturnTemp(self) -> float:
        return self._returnTemp
    
    def updateData(self):
        state = self._api.readRegister(self._register_handler.State, _subIndex = self.index)
        if state:
            self._state          = SentioHeatingStates(state)
        pump = self._api.readRegister(self._register_handler.PumpState, _subIndex = self.index)
        if pump:
            self._pumpState = PumpState(pump)
        self._inletMeasured  = self._api.readRegister(self._register_handler.MeasuredTemperature, _subIndex = self.index)
        if(self._inletMeasured == Defaults.InvalidFP2_100):
            self._inletMeasured = None
        self._inletDesired   = (self._api.readRegister(self._register_handler.DesiredInletTemperature, _subIndex = self.index))
        if(self._inletDesired == Defaults.InvalidFP2_100):
            self._inletDesired = None
        pass

    def printCircuit(self):
        logging.debug("HCC Circuit ID={0} | Name={1} || state {2}, Pump {3}, Inlet = {4} desired={5}, Return ={6}, Supplier ={7}".format(self.index, self.name, self._state, self._pumpState, self._inletMeasured, self._inletDesired, self._returnTemp, self._supplierTemp))
        print("HCC Circuit ID={0} | Name={1} || state {2}, Pump {3}, Inlet = {4} desired={5}, Return ={6}, Supplier ={7}".format(self.index, self.name, self._state, self._pumpState, self._inletMeasured, self._inletDesired, self._returnTemp, self._supplierTemp))