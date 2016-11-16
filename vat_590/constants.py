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

PRESSURE_READING = {
    'Negative': '-',
    'Positive': '0'
}

OPERATION = {
    'Normal operation': '0',
    'Simulation running': '1',
}

OPERATION_MODE = {
    'Local Operation': '0',
    'Remote Operation': '1',
    'Locked Remote Operation': '2'
}

WARNING = {
    'No warning': '0',
    'Warning present': '1'
}

STATUS = {
    'Initialization': '0',
    'Synchronization': '1',
    'Position control': '2',
    'Closed': '3',
    'Opened': '4',
    'Pressure control': '5',
    'Hold': '6',
    'Learn': '7',
    'Interlock (OPEN by digital input)': '8',
    'Interlock (CLOSED by digital input)': '9',
    'Power failure': 'C',
    'Safety mode': 'D',
    'Fatal error': 'E'
}

SERVICE = {
    'Not required': '0',
    'Requested': '1'
}

LEARN_DATA = {
    'Present': '0',
    'Not present': '1'
}

POWER_FAILURE_BATTERY = {
    'Ready': '0',
    'Not ready': '1'
}

COMPRESSED_AIR_SUPPLY = {
    'OK': '0',
    'Not OK': '1'
}

POSITION_RANGE_CODE = {
    '0 - 1000': '0',
    '0 - 10 000': '1',
    '0 - 100 000': '2'
}

BAUD_RATE = {
    '600': '0',
    '1200': '1',
    '2400': '2',
    '4800': '3',
    '9600': '4',
    '19.2k': '5',
    '38.4k': '6',
    '57.6k': '7',
    '115.2k': '8'
}

PARITY_BIT = {
    'even': '0',
    'odd': '1',
    'mark': '2',
    'space': '3',
    'no': '4'
}

DATA_LENGTH = {
    '7 bit': '0',
    '8 bit': '1'
}

STOP_BITS = {
    '1': '0',
    '2': '1'
}

DIGITAL_INPUT = {
    'not inverted': '0',
    'inverted': '1',
    'disabled': '2'
}

ERROR_INDEX = {
    'Parity error': 'E:000001:',
    'Input buffer overflow (too many characters)': 'E:000002:',
    'Framing error (data length, number of stop bits)': 'E:000003:',
    '<CR> or <LF> missing': 'E:000010:',
    ': missing': 'E:000011:',
    'Invalid number of characters (between : and <CR><LF>)': 'E:000012:',
    'Unknown command': 'E:000020:',
    'Unknown command': 'E:000021:',
    'Invalid value': 'E:000022:',
    'Invalid value': 'E:000023:',
    'Value out of range': 'E:000030:',
    'Command not applicable for hardware configuration': 'E:000041:',
    'Command not accepted due to local operation': 'E:000080:',
    'Command not accepted due to synchronization, CLOSED or OPEN by digital input, safety mode of fatal error': 'E:000082:'
}

CLOSE_OPEN = {
    'close': '0',
    'open': '1'
}

NO_YES = {
    'no': '0',
    'yes': '1'
}

VALVE_FAILURE_POSITION = {
    'valve will close': '0',
    'valve will open': '1',
    'valve stay on actual position': '2'
}

SYNCHRONIZATION_START = {
    'standard': '0',
    'special command': '1',
    'open command': '2',
    'all move commands': '3',
    'always': '4'
}

SYNCHRONIZATION_MODE = {
    'short': '0',
    'full': '1'
}

POWER_FAILURE_OPTION = {
    'power failure option not equipped': '0',
    'power failure option equipped': '1'
}

SENSOR_POWER_SUPPLY = {
    '+- 15V sensor power supply not equipped': '0',
    '+- 15V sensor power supply equipped': '1'
}

RS232_INTERFACE_ANALOG = {
    'RS232 interface without analog outputs': '2',
    'RS232 interface with analog outputs': '3'
}

SENSOR_VERSION = {
    '1 sensor version': '1',
    '2 sensor version': '2',
}
