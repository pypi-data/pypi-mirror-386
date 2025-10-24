import logging

from .SentioRegisterMap import *
from .ModbusWrapper import ModbusWrapper
from .SentioTypes import *
from .Defaults import Defaults

class SentioSensors:
    def __init__(self, api:ModbusWrapper):
        self._outdoorTemp = None
        self._hcsourceState = None
        
        self._deviceType = None
        self._serialNumber = None
        self._firmwareVersionMajor = None
        self._firmwareVersionMinor = None
        
        self._temperatureSensors = {}
        
        self._api = api
    
    def initialize(self):
        returnValue = 0
        try:
            deviceTypeInt = self._api.readRegister(SentioRegisterMap.Location.DeviceType)
            if deviceTypeInt:
                self._deviceType = SentioDeviceType(deviceTypeInt)
            else:
                self._deviceType = None

            serialNumberPrefix =  self._api.readRegister(SentioRegisterMap.Location.DeviceSerialNrPrefix)
            serialNumberNumber  = self._api.readRegister(SentioRegisterMap.Location.DeviceSerialNumber)
            serialNumberNumber = str(serialNumberNumber).zfill(Defaults.SerialNumberLength - Defaults.SerialNumberPrefixLen)
            self._serialNumber  = "{0}-{1}-{2}-{3}".format(serialNumberPrefix, serialNumberNumber[:2], serialNumberNumber[2:6], serialNumberNumber[6:10])

            self._firmwareVersionMajor = self._api.readRegister(SentioRegisterMap.Location.DeviceSwVersion)
            self._firmwareVersionMinor = self._api.readRegister(SentioRegisterMap.Location.DeviceSwVersionMinor)  

        except Exception as e:
            logging.error("Exception occured ==> {0}".format(e))
            returnValue = -1
        return returnValue

    def updateData(self):      
        #repetative values:
        self._outdoorTemp = self._api.readRegister(SentioRegisterMap.Outdoors.AirTemperature)
        if self._outdoorTemp and self._outdoorTemp == Defaults.InvalidFP2_100:
            self._outdoorTemp = None
        hcstate = self._api.readRegister(SentioRegisterMap.HCSource.State)
        if hcstate:
            self._hcsourceState = SentioHeatingStates(hcstate)
         
        for name, register in vars(SentioRegisterMap.HardwareIO.Thermistor).items():
            if isinstance(register, RegisterRepresentation):
                value = self._api.readRegister(register)
                if value != None and value != Defaults.InvalidFP2_100:
                    logging.debug("Success to read temperature sensor {0} with value {1}".format(name, value))
                    self._temperatureSensors[name] = value
                else:
                    logging.debug("Failed to read temperature sensor {0}".format(name))

    @property
    def outdoor_temperature(self) -> float:
        """Return outdoor temperature."""
        return self._outdoorTemp
    
    @property
    def hc_source_state(self) -> float:
        """Return H/C source state."""
        return self._hcsourceState

    @property
    def device_type(self) -> SentioDeviceType:
        return self._deviceType

    @property
    def serial_number(self):
        return self._serialNumber
    
    @property
    def firmware_version_major(self) -> int:
        return self._firmwareVersionMajor

    @property
    def firmware_version_minor(self) -> int:
        return self._firmwareVersionMinor

    @property
    def firmware_version_major(self) -> int:
        return self._firmwareVersionMajor
    
    @property
    def temperature_sensors(self) -> float | None:
        def inner(index):
            """Return a dictionary of temperature sensors and their values."""
            returnValue = None
            for name, value in self._temperatureSensors.items():
                if str(index) in name:
                    logging.debug("==> Update Return Value Sensor {0}[{1}] = {2} °C".format(name, index, value))
                    returnValue = value
            return returnValue
        return inner