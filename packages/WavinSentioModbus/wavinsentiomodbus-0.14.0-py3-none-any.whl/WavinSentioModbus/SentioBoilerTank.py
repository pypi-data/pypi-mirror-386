import logging

from .SentioRegisterMap import *
from .ModbusWrapper import ModbusWrapper
from .SentioTypes import *
from .Defaults import Defaults

class SentioBoilerTankHandler:
    def __init__(self, api:ModbusWrapper):
        self._boilerTanks = []
        self._api = api
        pass

    def initialize(self):
        self._boilerTanks=[]
        for tankCtr in range(Defaults.MaxNumberOfBoilerTanks):
            try:
                value = self._api.readRegister(SentioRegisterMap.DHWTanks.Name, _subIndex = tankCtr)
                if value != None:
                    self._boilerTanks.append(SentioBoilerTank(tankCtr, value, self._api, SentioRegisterMap.DHWTanks))
                else:
                    logging.error("Boiler Tank {0} not found".format(tankCtr))
            except Exception as e:
                logging.exception("Exception reading Boiler Tank Circuit {0}".format(e))
                return -1

        return 0
    
    def updateData(self):
        for tank in self._boilerTanks:
            tank.updateData()

class SentioBoilerTank:
    def __init__(self, index, name, api:ModbusWrapper, register_handler):
        self.index = index;
        self.name = name;
        self._state         = None
        self._currentTemp  = None
        self._desiredTemp  = None
        self._circulationState = None
        self._sourceInlet = None
        self._sourceOutlet = None
        self._cleaningTemperature = None
        self._temperatureSetpoint = None
        self._api = api
        self._register_handler = register_handler

    def GetIndex(self):
        return self.index
    
    @property
    def getCurrentTemp(self) -> float:
        return self._currentTemp
    
    @property
    def getDesiredTemp(self) -> float:
        return self._desiredTemp
    
    @property
    def getCirculationState(self) -> CirculationState:
        return self._circulationState
    
    @property
    def getSourceInlet(self) -> float:
        return self._sourceInlet    
    
    @property
    def getSourceOutlet(self) -> float:
        return self._sourceOutlet
    
    @property
    def getCleaningTemperature(self) -> float:
        return self._cleaningTemperature
    
    @property
    def getTemperatureSetpoint(self) -> float:
        return self._temperatureSetpoint
    
    def updateData(self):
        state = self._api.readRegister(self._register_handler.State, _subIndex = self.index)
        if state:
            self._state          = SentioHeatingStates(state)
        self._currentTemp = self._api.readRegister(self._register_handler.MeasuredTemperature, _subIndex = self.index)
        self._desiredTemp  = self._api.readRegister(self._register_handler.DesiredTemperature, _subIndex = self.index)
        circulationState = self._api.readRegister(self._register_handler.CirculationState, _subIndex = self.index)
        if circulationState != Defaults.Invalid_U8:
            logging.info("Boiler Tank {0} circulation state updated to {1}".format(self.index, circulationState))
            self._circulationState = CirculationState(circulationState)
        sourceInlet = self._api.readRegister(self._register_handler.SourceInletTemperature, _subIndex = self.index)
        if sourceInlet != Defaults.InvalidFP2_100:
            self._sourceInlet = sourceInlet
        sourceOutlet = self._api.readRegister(self._register_handler.SourceReturnTemperature, _subIndex = self.index)
        if sourceOutlet != Defaults.InvalidFP2_100:
            self._sourceOutlet = sourceOutlet
        cleaningTemperature = self._api.readRegister(self._register_handler.CleaningTemperature, _subIndex = self.index) 
        if cleaningTemperature != Defaults.InvalidFP2_100:
            self._cleaningTemperature = cleaningTemperature
        temperatureSetpoint = self._api.readRegister(self._register_handler.TemperatureSetpoint, _subIndex = self.index)
        if temperatureSetpoint != Defaults.InvalidFP2_100:
            self._temperatureSetpoint = temperatureSetpoint

    def printBoilerTank(self):
        logging.debug("Tank Circuit ID={0} | Name={1} || state {2}, CurrentTemp ={3}, DesiredTemp ={4}, CirculationState ={5}, SourceInlet ={6}, SourceOutlet ={7}, CleaningTemp ={8}, TempSetpoint ={9}".format(self.index, self.name, self._state, self._currentTemp, self._desiredTemp, self._circulationState, self._sourceInlet, self._sourceOutlet, self._cleaningTemperature, self._temperatureSetpoint))
        print("Tank Circuit ID={0} | Name={1} || state {2}, CurrentTemp ={3}, DesiredTemp ={4}, CirculationState ={5}, SourceInlet ={6}, SourceOutlet ={7}, CleaningTemp ={8}, TempSetpoint ={9}".format(self.index, self.name, self._state, self._currentTemp, self._desiredTemp, self._circulationState, self._sourceInlet, self._sourceOutlet, self._cleaningTemperature, self._temperatureSetpoint))