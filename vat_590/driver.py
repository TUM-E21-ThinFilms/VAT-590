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

from slave.driver import Driver, Command
from slave.types import String, Mapping, BitSequence
from protocol import VAT590Protocol
from constants import *

class VAT590Driver(object):

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

        self._transport = transport
        self._protocol = protocol
        #super(VAT590Driver, self)._init_(transport, protocol)

        self.PID_controller = Command(
            'i:02',
            's:02',
            String
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

        self._device_status = Command(('i:30', BitSequence([
            (1, Mapping(OPERATION_MODE)),  # Operation mode
            (1, Mapping(STATUS)),  # Status
            (1, Mapping(POWER_FAILURE_BATTERY)),  # Power failure option
            (1, Mapping(OPERATION))  # Operation
        ])))

        self._assembly = Command('i:76', 'i:76', BitSequence([
            (6, String()),  # Position
            (1, Mapping(PRESSURE_READING)),  # Pressure reading
            (7, String()),  # Pressure
            (1, Mapping(OPERATION_MODE)),  # Operation mode
            (1, Mapping(STATUS)),  # Status
            (1, Mapping(WARNING))  # Warning
        ]))

        self._warnings = Command(('i:51', BitSequence([
            (1, Mapping(SERVICE)),  # Service
            (1, Mapping(LEARN_DATA)),  # Learn data set
            (1, Mapping(POWER_FAILURE_BATTERY)),  # Power failure battery
            (1, Mapping(COMPRESSED_AIR_SUPPLY))  # Compressed air supply
        ])))

        self._valve_configuration = Command('i:04', 's:04', BitSequence([
            (1, Mapping(CLOSE_OPEN)),  # VALVE_POWER_UP
            (1, Mapping(CLOSE_OPEN)),  # VALVE_POWER_FAILURE
            (1, Mapping(NO_YES)),  # EXTERNAL_ISOLATION_VALVE_FUNCTION
            (1, Mapping(NO_YES)),  # CONTROL_STROKE_LIMITATION
            (1, Mapping(VALVE_FAILURE_POSITION)),  # NETWORK_FAILURE_END_POSITION
            (1, Mapping(VALVE_FAILURE_POSITION)),  # SLAVE_OFFLINE_POSITION
            (1, Mapping(SYNCHRONIZATION_START)),
            (1, Mapping(SYNCHRONIZATION_MODE)),
        ]))

        self._errors = Command(('i:50', Mapping({
            'No errors': '00000000',
            'Sensor 1 signal converter failure.': '01000000',
            'Firmware memory failure.': '00010000'
        })))

        self._range_config = Command('i:21', 's:21', BitSequence([
            (1, String()),  # Position range
            (7, String()),  # Pressure range
        ]))

        self._sensor_configuration = Command('i:01', 's:01', BitSequence([
            (1, String()),
            (1, String()),
            (6, String())    
        ]))

        self._sensor_reading = Command('i:64', 'i:64', String)
        self._sensor_offset = Command('i:60', 'i:60', String)
        self._speed = Command('i:68', 'V:', String)
        self._pressure = Command('P:', 'S:', String)
        self._position = Command('A:', 'R:', String)
        self._identification = Command(('i:83', String))
        self._firmware_number = Command(('i:84', String))
        self._firmware_config = Command(('i:82', String))
        self._pressure_alignment = Command('c:6002', 'c:6002', String)
        self._zero = ('Z:', String)
        self._learn = ('L:0', String)

        # write only commands
        self._hold = ('H:', String)
        self._reset = ('c:82', String)
        self._close = ('C:', String)
        self._open = ('O:', String)
        self._access_mode = ('c:01', String)

    def clear(self):
        self._protocol.clear(self._transport)

    def _query(self, cmd):
        if not isinstance(cmd, Command):
            raise TypeError("Can only query on Command")

        return cmd.query(self._transport, self._protocol)

    def _write(self, cmd, *datas):
        if not isinstance(cmd, Command):
            cmd = Command(write=cmd)

        cmd.write(self._transport, self._protocol, *datas)

    def get_firmware_configuration(self):
        return self._query(self._firmware_config)

    def get_firmware_number(self):
        self._query(self._firmware_number)

    def get_identification(self):
        return self._query(self._identification)

    def get_assembly(self):
        return self._query(self._assembly)

    def get_device_status(self):
        return self._query(self._device_status)

    def get_warnings(self):
        return self._query(self._warnings)

    def get_errors(self):
        return self._query(self._errors)

    def get_position(self):
        return int(self._query(self._position))

    def get_valve_configuration(self):
        return self._query(self._valve_configuration)

    # Warning: Read the documents for the valve, in order to send
    # a correct configuration!
    # There are no checks for correctness!
    def set_valve_configuration(self, configuration):
        self._write(self._valve_configiguration, configuration)

    def set_position(self, setpoint):
        if not isinstance(setpoint, (int, long)):
            raise TypeError("setpoint must be an integer")

        if setpoint < 0 or setpoint > 1000000:
            raise ValueError("setpoint must be in range (0, 1'000'000)")

        self._write(self._position, str(setpoint).zfill(6))

    def get_sensor_offset(self):
        return int(self._query(self._sensor_offset))

    def get_sensor_reading(self):
        return int(self._query(self._sensor_reading))

    def get_pressure(self):
        return int(self._query(self._pressure))

    def set_pressure(self, setpoint):
        if not isinstance(setpoint, (int, long)):
            raise TypeError("setpoint must be an integer")

        if setpoint < 0 or setpoint > 100000000:
            raise ValueError("setpoint must be in (0, 100'000'000), given: %s" % str(setpoint))

        self._write(self._pressure, str(setpoint).zfill(8))

    def hold(self):
        self._write(self._hold, '')

    def reset(self, mode=None):
        if mode is None:
            mode = self.RESET_FATAL_ERROR

        if mode not in [self.RESET_FATAL_ERROR, self.RESET_WARNINGS]:
            raise ValueError("Wrong reset mode, see RESET_* constants")

        return self._write(self._reset, mode)

    def close(self):
        self._write(self._close, '')

    def open(self):
        self._write(self._open, '')

    def set_access(self, mode):
        if mode not in [self.ACCESS_MODE_LOCAL, self.ACCESS_MODE_LOCKED_REMOTE, self.ACCESS_MODE_REMOTE]:
            raise ValueError("Wrong access mode, see ACCESS_MODE_* constants")

        self._write(self._access_mode, mode)

    def get_speed(self):
        return int(self._query(self._speed))

    def set_speed(self, speed):
        if not isinstance(speed, (int, long)) or speed >= 10000:
            raise ValueError("Input value too precise or more than 4 digits used")

        self._write(self._speed, str(speed).zfill(6))

    def get_pressure_range(self):
        return int(self.get_range_configuration()[1])

    def get_position_range(self):
        return int(self.get_range_configuration()[0])

    def get_range_configuration(self):
        return self._query(self._range_config)

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

        self._write(self._range_config, "".join([position_range, str(pressure_range).zfill(7)]))

    def set_pressure_alignment(self, setpoint):
        if not isinstance(setpoint, (int, long)):
            raise TypeError("setpoint must be an integer")

        if setpoint < 0 or setpoint > 100000000:
            raise ValueError("setpoint must be in (0, 100'000'000), given: %s" % str(setpoint))

        self._write(self._pressure_alignment, str(setpoint).zfill(8))

    def zero(self):
        self._write(self._zero, '')	

    def learn(self, setpoint):
        if not isinstance(setpoint, (int, long)):
            raise TypeError("setpoint must be an integer")

        if setpoint < 0 or setpoint > 100000000:
            raise ValueError("setpoint must be in range (0, 100'000'000), given: %s" % str(setpoint))

        self._write(self._learn, str(setpoint).zfill(8))
        
    def get_sensor_configuration(self):
        return self._query(self._sensor_configuration)

    def set_sensor_configuration(self, config):
        if not len(config) == 3:
            raise ValueError("config must be of format like `get_sensor_configuration`")
        # this creates an error in log file (Unexpected response 's:01') this error can be discarded
        # Notice that the slave lib expects no response when 'setting' values
        # But the VAT590 returns after a set-operation an response.
        self._write(self._sensor_configuration, "".join(config))
	
