from time import sleep_ms
from struct import pack, unpack


DEVICE_ADDRESS = 0x36

REG_DesignCap = 0x18            # Design Capacity
REG_ModelCfg = 0xDB             # Configuration for "ModelGauge m5 EZ" algorithm
REG_IChgTerm = 0x1E             # Termination Current
REG_FStat = 0x3D                # Flag Status

REG_RepCap = 0x05               # Reported Capacity
REG_RepSOC = 0x06               # Reported State of Charge
REG_TTE = 0x11                  # Time to Empty
REG_TTF = 0x20                  # Time to Full
REG_VCell = 0x09                # Cell Voltage
REG_Current = 0x0A              # Current
REG_DieTemp = 0x34              # Die Temperature

LSB_PERCENTAGE = 1.0/256.0      # Percentage %
LSB_VOLTAGE = 1.25/16.0         # Voltage mV
LSB_TEMPERATURE = 1.0/256.0     # Temperature C
LSB_TIME = 5.625                # Time s
LSB_CAPACITY_R = 0.5            # Capacity mAh
LSB_CAPACITY_H = 0.1667         # Capacity mAh
LSB_CURRENT_R = 156.25          # Current uA
LSB_CURRENT_H = 52.083          # Current uA
LSB_RESISTANCE_R = 1.0/4096.0   # Resistance Ohm
LSB_RESISTANCE_H = 1.0/12288.0  # Resistance Ohm


class MAX17262:
    """Minimal driver for the MAX17262 battery gauge IC.
    This driver is based on the datasheet from Maxim Integrated and supports both
    the R and H type ICs. The main difference between the two is the value range
    of the current, resitance and capacity registers.
    This software only implements the most basic functionality to operate the IC in
    its default settings, without any calibration or specific battery profiles.
    However the IC is pretty good in estimating the battery capacity and state of
    charge.
    """
    def __init__(
            self,
            i2c,
            capacity,
            terminationCurrent,
            lowVoltage=True,
            address=DEVICE_ADDRESS,
            is_r_type=True
            ):
        """Initialize the MAX17262 IC.
        i2c: The I2C bus object to use.
        capacity: The capacity of the battery in mAh.
        terminationCurrent: charge termination current in micro ampere (uA).
        lowVoltage: True for charge voltage below 4.25V, False otherwise.
        address: The I2C address of the IC.
        is_r_type: True for R type IC, False for H type IC."""

        self.i2c = i2c
        self.address = address
        self.is_r_type = is_r_type

        # wait while the "data not ready (DNR)" bit is cleared
        # this taken from the user guide, the datasheet does not mention this
        while self.read_uint16(REG_FStat) & 0x0001:
            sleep_ms(10)

        if is_r_type:
            cap = int(capacity / LSB_CAPACITY_R)
            cur = int(terminationCurrent / LSB_CURRENT_R)
        else:
            cap = int(capacity / LSB_CAPACITY_H)
            cur = int(terminationCurrent / LSB_CURRENT_H)
        
        # set the battery parameters for the ic to use
        self.i2c.writeto_mem(self.address, REG_DesignCap, pack("<H", cap))
        self.i2c.writeto_mem(self.address, REG_IChgTerm, pack("<h", cur))

        # reset the ic and set the appropriate charging voltage
        if lowVoltage:
            self.i2c.writeto_mem(self.address, REG_ModelCfg, b"\x00\x80")
        else:
            self.i2c.writeto_mem(self.address, REG_ModelCfg, b"\x00\x84")

        # wait for the ic to clear the reset bit
        # this is also taken from the user guide
        while self.read_uint16(REG_ModelCfg) & 0x8000:
            sleep_ms(10)

    def read_int16(self, mem_addr):
        data = self.i2c.readfrom_mem(self.address, mem_addr, 2)
        return unpack("<h", data)[0]

    def read_uint16(self, mem_addr):
        data = self.i2c.readfrom_mem(self.address, mem_addr, 2)
        return unpack("<H", data)[0]

    @property
    def state_of_charge(self):
        """Returns the state of charge in percent."""
        return self.read_uint16(REG_RepSOC) * LSB_PERCENTAGE

    @property
    def time_to_empty(self):
        """Returns the time to empty in seconds."""
        return self.read_uint16(REG_TTE) * LSB_TIME

    @property
    def time_to_full(self):
        """Returns the time to full in seconds."""
        return self.read_uint16(REG_TTF) * LSB_TIME

    @property
    def current(self):
        """Returns the current in uA."""
        if self.is_r_type:
            return self.read_int16(REG_Current) * LSB_CURRENT_R
        else:
            return self.read_int16(REG_Current) * LSB_CURRENT_H

    @property
    def voltage(self):
        """Returns the cell voltage in mV."""
        return self.read_uint16(REG_VCell) * LSB_VOLTAGE

    @property
    def capacity(self):
        """Returns the remaining capacity in mAh."""
        if self.is_r_type:
            return self.read_uint16(REG_RepCap) * LSB_CAPACITY_R
        else:
            return self.read_uint16(REG_RepCap) * LSB_CAPACITY_H

    @property
    def temperature(self):
        """Returns the die temperature in degrees Celsius."""
        return self.read_int16(REG_DieTemp) * LSB_TEMPERATURE
