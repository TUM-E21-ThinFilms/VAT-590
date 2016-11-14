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
from slave.types import Integer, String, Register, Enum, Mapping, Float, Range, Register, Percent, BitSequence
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

    def __init__(self, transport, protocol=None):

        if protocol is None:
            protocol = VAT590Protocol()

        super(VAT590Driver, self).__init__(transport, protocol)

        # Range configuration:

        self._position_range = '2'  # Position Range: 0: <= 1000, 1: <=10 000, 2: <= 100 000
        self._pressure_range = '1000000'
        self._sensor_offset = 0.04

        # Commands:

        self.assembly = Command(
            ('i:76',
             BitSequence([
                 (6, Percent(self._position_range, 6)),  # Position
                 (1, Mapping(PRESSURE_READING)),  # Pressure reading
                 (7, String()),  # Pressure
                 (1, Mapping(OPERATION_MODE)),  # Operation mode
                 (1, Mapping(STATUS)),  # Status
                 (1, Mapping(WARNING))  # Warning
             ])
             )
        )

        self._pressure = Command(
            'P:',
            'S:',
            String
        )

        self.device_status = Command(
            ('i:30',
             BitSequence([
                 (1, Mapping(OPERATION_MODE)),  # Operation mode
                 (1, Mapping(STATUS)),  # Status
                 (1, Mapping(POWER_FAILURE_BATTERY)),  # Power failure option
                 (1, Mapping(OPERATION))  # Operation
             ])
             )
        )

        self.warnings = Command(
            ('i:51',
             BitSequence([
                 (1, Mapping(SERVICE)),  # Service
                 (1, Mapping(LEARN_DATA)),  # Learn data set
                 (1, Mapping(POWER_FAILURE_BATTERY)),  # Power failure battery
                 (1, Mapping(COMPRESSED_AIR_SUPPLY))  # Compressed air supply
             ])
             )
        )

        self.error_status = Command(
            ('i:52',
             Mapping({'No errors': '00000000',
                      'Sensor 1 signal converter failure.': '01000000',
                      'Firmware memory failure.': '00010000'}))
        )

        self.fatal_error_query = Command(
            ('i:50',
             Mapping({'No errors.': '000',
                      'Fatal error: Limit stop of valve unit not detected.': '020',
                      'Fatal error: Rotation angle of valve plate limited during operation.': '022',
                      'Fatal error: Motor driver failure detected.': '040'}))
        )

        self.throttle_cycles = Command(
            ('i:70',
             Integer)
        )

        self.isolation_cycles = Command(
            ('i:71',
             Integer)
        )

        self.power_up_counter = Command(
            ('i:72',
             Integer)
        )

        self.hardware_config = Command(  #####
            ('i:80',
             String()
             #           BitSequence([
             #                (1, Mapping(POWER_FAILURE_OPTION)),
             #                (1, Mapping(SENSOR_POWER_SUPPLY)),
             #                (1, Mapping(RS232_INTERFACE_ANALOG)),
             #                (1, Mapping(SENSOR_VERSION)),
             #                (4, String) # reserved
             #                ])
             )
        )

        self.firmware_config = Command(
            ('i:82',
             String)
        )

        self.firmware_number = Command(
            ('i:84',
             String)
        )

        self.identification = Command(
            ('i:83',
             String)
        )

        self.PID_controller = Command(
            # Command: def __init__(self, query=None, write=None, type_=None, protocol=None):
            'i:02',
            's:02',
            String
            # Integer (fmt='{:0>8d}')
        )

        self._range_config = Command(
            'i:21',
            's:21',
            # String()
            BitSequence([
                (1, String()),  # Position range
                (7, String()),  # Pressure range
            ])
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

        self.valve_config = Command(
            'i:04',
            's:04',
            BitSequence([
                (1, Mapping(CLOSE_OPEN)),  # VALVE_POWER_UP
                (1, Mapping(CLOSE_OPEN)),  # VALVE_POWER_FAILURE
                (1, Mapping(NO_YES)),  # EXTERNAL_ISOLATION_VALVE_FUNCTION
                (1, Mapping(NO_YES)),  # CONTROL_STROKE_LIMITATION
                (1, Mapping(VALVE_FAILURE_POSITION)),  # NETWORK_FAILURE_END_POSITION
                (1, Mapping(VALVE_FAILURE_POSITION)),  # SLAVE_OFFLINE_POSITION
                (1, Mapping(SYNCHRONIZATION_START)),
                (1, Mapping(SYNCHRONIZATION_MODE)),
            ])
        )

        self.position = Command(
            'A:',
            'R:',
            Percent(self._position_range, 6)
        )

        self.position_limit = Command(  # kann sein dass hier Leerzeichen auftreten... # FUNKTIONIERT NICHT!!!
            'a101A:',
            'a101A:',
            String()  # 0 - 100 000
        )

        self._speed = Command(
            'i:68',
            'V:',
            String
        )

    # Properties:

    @property
    def speed(self):
        return float(self._speed) / 10

    @speed.setter
    def speed(self, value):
        value *= 10
        if (int(value) != value):
            raise ValueError("Warning! Input value too precise! Precision: One decimal!")
        self._speed = '00' + '{:0>4.0f}'.format(value)

    @property
    def position_range(self):
        return self._range_config[0]

    @position_range.setter
    def position_range(self, value):
        self._position_range = str(value)
        self._range_config[0] = self._position_range

    @property
    def pressure_range(self):
        return self._range_config[1]

    @pressure_range.setter
    def pressure_range(self, value):
        self._pressure_range = '{:0>7d}'.format(value)
        self._range_config[1] = self._pressure_range

    @property
    def pressure(self):
        volt = (int(self._pressure) / (
        int(self._pressure_range) / 10.0)) + self._sensor_offset  # voltage signal from gauge
        output = pow(10, 1.667 * volt - 11.33)  # Calculated with formula from Pfeiffer
        if output < 1e-9:
            self.close()  # Close valve!
            print ('Connection Error! Check Sensor cables!')
        if output > 1:
            self.close()  # Close valve!
            print ('Pressure too high! Valve closed!')
        return "%.2e" % (output)

    @pressure.setter
    def pressure(self, value):
        if value < 0:
            raise ValueError('Negative input! (' + str(value) + ' mbar)')
        if value > 1:
            raise ValueError('Pressure input is too high! Maximum pressure: 1 mbar')
        volt = str(
            6.8 + 0.6 * log10(value) - self._sensor_offset)  # Spannungs-Wert aus Druckeingabe berechnen, mit Offset
        volt = volt.replace('.', '')  # Remove the dot
        volt = ('{0:0<6}').format(volt)  # von rechts auffüllen
        volt = volt[:int(len(str(int(self._pressure_range))) - 1)]  # abschneiden, dabei Präzision berücksichtigen
        volt = '00' + ('{0:0>6}').format(volt)  # von links auffüllen
        self._pressure = volt  # Wert übergeben
        print ('Pressure set to ' + str(value) + ' mbar.')

    # Functions:

    def access_mode_set(self):
        cmd = 'c:01', String
        self._write(cmd, '01')
        print 'VAT_Valve: Access mode set.'

    def reconfig(self):
        self.access_mode_set()
        time.sleep(.1)
        self.interface_config = ['9600', 'even', '7 bit', '1', 'Reserved', 'not inverted', 'not inverted', 'Reserved']
        print ('Vat_Valve: Interface configuration set.')
        time.sleep(.1)
        self._range_config = [self._position_range, self._pressure_range]
        print ('Vat_Valve: Range configuration set: ')

    def reset(self, value=1):
        cmd = 'c:82', String
        return self._write(cmd, '0' + str(value))

    def close(self):
        cmd = 'C:', String
        return self._write(cmd, '')

    def open(self):
        if self.pressure < 100:
            raise ValueError('Chamber is evacuated, do not open the leak valve!')
        cmd = 'O:', String
        return self._write(cmd, '')

    def hold(self):
        cmd = 'H:', String
        return self._write(cmd, '')

    def error_table(self):
        return ERROR_INDEX

    def learn(self, value):  # Pressure limit for learn has to be transmitted
        cmd = 'L:0', String
        return self._write(cmd, str(value))