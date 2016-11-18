# Copyright (C) 2016, see AUTHORS.md
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time

from math import log10
from slave.driver import Driver, Command
from slave.types import Integer, String, Mapping, BitSequence
from protocol import VAT590Protocol
from constants import *


class VAT590Driver(Driver):
    """ The Control Programme for the VAT Valve Series 590

    .. note::
        The valve needs carriage return and linefeed character as message terminator. Using delay between read and write operations is recommended as well.

        Internal variables starting with "_" expect and provide String codes (VAT control commands).
        Variables with the same names but without "_" expect and provide readable information. (Realized by properties and property setters)


    :param transport: A transport object.

    :ivar position_range: Range setting for valve position; '0': 0-1000, '1': 0-10 000, '2': 0-100 000.
    :ivar pressure_range: Range for pressure readings: The output number is the number for the highest pressure.
    :ivar assembly: Returns the position, pressure reading, pressure, operation mode, status and warnings.
    :ivar pressure: Returns the pressure
    :ivar device_status: Returns the operation mode, status, power failure option and operation.
    :ivar warnings: Returns warnings.
    :ivar error_status: Return the error status.
    :ivar fatal_error_query: Returns fatal errors if there are some.
    :ivar throttle_cycles: Returns the number of throttle cycles.
    :ivar power_up_counter: Returns the number of control unit power ups.
    :ivar firmware_configuration: Returns the firmware version of the device.
    :ivar identification: Returns an identification code, this code is unique for each valve and allows tracing.
    :ivar PID_controller: this command selects gain factor, sensor response time and setpoint ramp for the PID.
    :ivar range_configuration: Returns the position range setting and pressure reading (variables _position_range and _pressure_range, respectively).
    :ivar interface_configuration: Returns the baud rate, parity bit, data length, number of stop bits, digital input OPEN valve and digital
            input CLOSED valve.
    :ivar position: Returns the position of the valve in percent.
    :ivar speed: Return the speed of the valve in percent.

    :ifunc access_mode_set(): Set the valve to access mode.
    :ifunc reconfig(): Reconfigures the valve with the actual range settings.
    :ifunc reset(param = '1'): Resets the valve; param '0': Reset service request bit from warnings, param '1': Restart control unit
    :ifunc close(): Closes the valve.
    :ifunc open(): Opens the valve.
    :ifunc hold(): Stops the valve at the current position.
    :ifunc error_table(): Returns a table with the meanings of errors (e.g. E:000001<CR><LF> : Parity error).

    """

    RESET_WARNINGS = '00'
    RESET_FATAL_ERROR = '01'

    ACCESS_MODE_LOCAL = '00'
    ACCESS_MODE_REMOTE = '01'
    ACCESS_MODE_LOCKED_REMOTE = '02'

    RANGE_POSITION_1000 = '0'
    RANGE_POSITION_10000 = '1'
    RANGE_POSITION_100000 = '2'

    def __init__(self, transport, protocol=None):

        if protocol is None:
            protocol = VAT590Protocol()

        super(VAT590Driver, self).__init__(transport, protocol)

        # Range configuration:

        # self._position_range = '2'  # Position Range: 0: <= 1000, 1: <=10 000, 2: <= 100 000
        # self._pressure_range = '1000000'
        # self._sensor_offset = 0.04

        self.PID_controller = Command(
            'i:02',
            's:02',
            String
            # Integer (fmt='{:0>8d}')
        )

        self.interface_config = Command(
            'i:20',
            's:20',
            BitSequence([
                (1, Mapping(BAUD_RATE)),  # Baud rate
                (1, Mapping(PARITY_BIT)),  # Parity bit
                (1, Mapping(DATA_LENGTH)),  # Data length
                (1, Mapping(STOP_BITS)),  # Number of stop bits
                (1, Mapping({'Reserved': '0'})),
                (1, Mapping(DIGITAL_INPUT)),  # Digital input OPEN valve
                (1, Mapping(DIGITAL_INPUT)),  # Digital input CLOSED valve
                (1, Mapping({'Reserved': '0'}))
            ])
        )

        self.__device_status = Command(('i:30', BitSequence([
            (1, Mapping(OPERATION_MODE)),  # Operation mode
            (1, Mapping(STATUS)),  # Status
            (1, Mapping(POWER_FAILURE_BATTERY)),  # Power failure option
            (1, Mapping(OPERATION))  # Operation
        ])))

        self.__assembly = Command('i:76', 'i:76', BitSequence([
            (6, String),  # Position
            (1, Mapping(PRESSURE_READING)),  # Pressure reading
            (7, String()),  # Pressure
            (1, Mapping(OPERATION_MODE)),  # Operation mode
            (1, Mapping(STATUS)),  # Status
            (1, Mapping(WARNING))  # Warning
        ]))

        self.__warnings = Command(('i:51', BitSequence([
            (1, Mapping(SERVICE)),  # Service
            (1, Mapping(LEARN_DATA)),  # Learn data set
            (1, Mapping(POWER_FAILURE_BATTERY)),  # Power failure battery
            (1, Mapping(COMPRESSED_AIR_SUPPLY))  # Compressed air supply
        ])))

        self.__valve_configiguration = Command('i:04', 's:04', BitSequence([
            (1, Mapping(CLOSE_OPEN)),  # VALVE_POWER_UP
            (1, Mapping(CLOSE_OPEN)),  # VALVE_POWER_FAILURE
            (1, Mapping(NO_YES)),  # EXTERNAL_ISOLATION_VALVE_FUNCTION
            (1, Mapping(NO_YES)),  # CONTROL_STROKE_LIMITATION
            (1, Mapping(VALVE_FAILURE_POSITION)),  # NETWORK_FAILURE_END_POSITION
            (1, Mapping(VALVE_FAILURE_POSITION)),  # SLAVE_OFFLINE_POSITION
            (1, Mapping(SYNCHRONIZATION_START)),
            (1, Mapping(SYNCHRONIZATION_MODE)),
        ]))

        self.__errors = Command(('i:50', Mapping({
            'No errors': '00000000',
            'Sensor 1 signal converter failure.': '01000000',
            'Firmware memory failure.': '00010000'
        })))

        self.__range_config = Command('i:21', 's:21', BitSequence([
            (1, String()),  # Position range
            (7, String()),  # Pressure range
        ]))

        self.__sensor_reading = Command('i64', 'i64', String)
        self.__sensor_offset = Command('i:60', 'i60', String)
        self.__speed = Command('i:68', 'V:', String)
        self.__pressure = Command('P:', 'S:', String)
        self.__position = Command('A:', 'R:', String)
        self.__identification = Command(('i:83', String))
        self.__firmware_number = Command(('i:84', String))
        self.__firmware_config = Command(('i:82', String))

        # write only commands
        self.__hold = ('H:', String)
        self.__reset = ('c:82', String)
        self.__close = ('C:', String)
        self.__open = ('O:', String)
        self.__access_mode = ('c:01', String)

    def __query(self, cmd):
        return cmd.query(self._transport, self._protocol)

    def get_firmware_configuration(self):
        return self.__query(self.__firmware_config)

    def get_firmware_number(self):
        self.__query(self.__firmware_number)

    def get_identification(self):
        return self.__query(self.__identification)

    def get_assembly(self):
        return self.__query(self.__assembly)

    def get_device_status(self):
        return self.__query(self.__device_status)

    def get_warnings(self):
        return self.__query(self.__warnings)

    def get_errors(self):
        return self.__query(self.__errors)

    def get_position(self):
        return self.__query(self.__position)

    def get_valve_configuration(self):
        return self.__query(self.__valve_configiguration)

    # Warning: Read the documents for the valve, in order to send
    # a correct configuration!
    # There are no checks for correctness!
    def set_valve_configuration(self, configuration):
        self._write(self.__valve_configiguration, configuration)

    def set_position(self, setpoint):
        if not isinstance(setpoint, (int, long)):
            raise TypeError("setpoint must be an integer")

        if not setpoint > 0 or setpoint < 1000000:
            raise ValueError("setpoint must be in range (0, 1'000'000)")

        self._write(self.__position, str(setpoint).zfill(6))

    def get_sensor_offset(self):
        return int(self.__query(self.__sensor_offset))

    def get_sensor_reading(self):
        return int(self.__query(self.__sensor_reading))

    def get_pressure(self):
        return int(self.__query(self.__pressure))

    def set_pressure(self, setpoint):
        if not isinstance(setpoint, (int, long)):
            raise TypeError("setpoint must be an integer")

        if setpoint < 0 or setpoint < 100000000:
            raise ValueError("setpoint must be in (0, 100'000'000)")

        self._write(self.__pressure, str(setpoint).zfill(8))

    def hold(self):
        self._write(self.__hold)

    def reset(self, mode=None):
        if mode is None:
            mode = self.RESET_FATAL_ERROR

        if mode not in [self.RESET_FATAL_ERROR, self.RESET_WARNINGS]:
            raise ValueError("Wrong reset mode, see RESET_* constants")

        return self._write(self.__reset, mode)

    def close(self):
        self._write(self.__close)

    def open(self):
        self._write(self.__open)

    def set_access(self, mode):
        if mode not in [self.ACCESS_MODE_LOCAL, self.ACCESS_MODE_LOCKED_REMOTE, self.ACCESS_MODE_REMOTE]:
            raise ValueError("Wrong access mode, see ACCESS_MODE_* constants")

        self._write(self.__access_mode, mode)

    def get_speed(self):
        return int(self.__query(self.__speed))

    def set_speed(self, speed):
        if not isinstance(speed, (int, long)) or speed >= 10000:
            raise ValueError("Input value too precise or more than 4 digits used")

        self._write(self.__speed, str(speed).zfill(6))

    def get_pressure_range(self):
        return self.get_range_configuration()[1]

    def get_position_range(self):
        return self.get_range_configuration()[0]

    def get_range_configuration(self):
        return self.__query(self.__range_config)

    def convert_from_range_configuration(self, range):
        if range is self.RANGE_POSITION_1000:
            return 1000
        elif range is self.RANGE_POSITION_10000:
            return 10000
        elif range is self.RANGE_POSITION_100000:
            return 100000
        else:
            raise ValueError("given range is not supported")

    def convert_to_range_configuration(self, range):
        if range is 1000:
            return self.RANGE_POSITION_1000
        elif range is 10000:
            return self.RANGE_POSITION_10000
        elif range is 100000:
            return self.RANGE_POSITION_100000
        else:
            raise ValueError("given range is not supported")

    def set_range_configuration(self, position_range, pressure_range):
        if not position_range in [self.RANGE_POSITION_1000, self.RANGE_POSITION_10000, self.RANGE_POSITION_100000]:
            raise ValueError("position range not valid, see RANGE_POSITION_* constants")

        if not isinstance(pressure_range, (int, long)):
            raise TypeError("pressure range must be an integer")

        if pressure_range < 1000 or pressure_range > 1000000:
            raise ValueError("pressure range out of range: [1000, 100'000]")

        self._write(self.__range_config, "".join([position_range, str(pressure_range).zfill(7)]))

        # @position_range.setter
        # def position_range(self, value):
        #    self._position_range = str(value)
        #    self._range_config[0] = self._position_range
        #
        #    @property
        #    def pressure_range(self):
        #        return self._range_config[1]
        #
        #    @pressure_range.setter
        #    def pressure_range(self, value):
        #        self._pressure_range = '{:0>7d}'.format(value)
        #        self._range_config[1] = self._pressure_range
        #
        #   @property
        #   def pressure(self):
        #       volt = (int(self._pressure) / (
        #           int(self._pressure_range) / 10.0)) + self._sensor_offset  # voltage signal from gauge
        #       output = pow(10, 1.667 * volt - 11.33)  # Calculated with formula from Pfeiffer
        #       if output < 1e-9:
        #           self.close()  # Close valve!
        #           print ('Connection Error! Check Sensor cables!')
        #       if output > 1:
        #           self.close()  # Close valve!
        #           print ('Pressure too high! Valve closed!')
        #       return "%.2e" % (output)
        #
        #    @pressure.setter
        #    def pressure(self, value):
        #        if value < 0:
        #            raise ValueError('Negative input! (' + str(value) + ' mbar)')
        #        if value > 1:
        #            raise ValueError('Pressure input is too high! Maximum pressure: 1 mbar')
        #        volt = str(
        #            6.8 + 0.6 * log10(value) - self._sensor_offset)  # Spannungs-Wert aus Druckeingabe berechnen, mit Offset
        #        volt = volt.replace('.', '')  # Remove the dot
        #        volt = ('{0:0<6}').format(volt)  # von rechts auffuellen
        #        volt = volt[:int(len(str(int(self._pressure_range))) - 1)]  # abschneiden, dabei Praezision beruecksichtigen
        #        volt = '00' + ('{0:0>6}').format(volt)  # von links auffuellen
        #        self._pressure = volt  # Wert uebergeben
        #        print ('Pressure set to ' + str(value) + ' mbar.')
        #
        #    # Functions:
        #
        #    def reconfig(self):
        #        self.access_mode_set()
        #        time.sleep(.1)
        #        self.interface_config = ['9600', 'even', '7 bit', '1', 'Reserved', 'not inverted', 'not inverted', 'Reserved']
        #        print ('Vat_Valve: Interface configuration set.')
        #        time.sleep(.1)
        #        self._range_config = [self._position_range, self._pressure_range]
        #        print ('Vat_Valve: Range configuration set: ')
        #
        #    def error_table(self):
        #        return ERROR_INDEX
        #
        #    def learn(self, value):  # Pressure limit for learn has to be transmitted
        #        cmd = 'L:0', String
        #        return self._write(cmd, str(value))


        #    @speed.setter
        #    def speed(self, value):
        #        value *= 10
        #        if (int(value) != value):
        #            raise ValueError("Warning! Input value too precise! Precision: One decimal!")
        #        self._speed = '00' + '{:0>4.0f}'.format(value)

        # @property
        # def position_range(self):
        #    return self._range_config[0]


        #    @property
        #    def speed(self):
        #        return float(self._speed) / 10
