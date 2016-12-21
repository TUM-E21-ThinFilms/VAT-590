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

from slave.protocol import Protocol
from slave.transport import Timeout

import e21_util
from e21_util.lock import InterProcessTransportLock
from e21_util.error import CommunicationError

class VAT590Protocol(Protocol):

    def __init__(self, logger=None):
        self.logger = logger
        self.encoding = 'ascii'

    def create_message(self, header, *data):
        msg = []
        msg.append(header)
        msg.extend(data)
        msg.append("\r\n")
        return ''.join(msg).encode(self.encoding)

    def parse_response(self, response, header):
        response = response.decode(self.encoding)

        if not response.startswith(header[0]):
            raise ValueError('Response header mismatch: received "' + str(response) + '" expected: "' + str(header[0]) + '"')

        response = response[len(header):]
        return response.split(None)

    def read_response(self, transport):
        try:
            resp = transport.read_until("\r\n")
            self.logger.debug('Response: "%s"', repr(resp))
            return resp
        except:
            raise CommunicationError("Could not read response")

    def send_message(self, transport, raw_data):
        try:
            self.logger.debug('Sending: "%s"', repr(raw_data))
            transport.write(raw_data)
        except:
            raise CommunicationError("Could not send data")

    def query(self, transport, header, *data):
        with InterProcessTransportLock(transport):
            message = self.create_message(header, *data)
            with transport:
                self.send_message(transport, message)
                response = self.read_response(transport)

            return self.parse_response(response, header)

    def write(self, transport, header, *data):
        with InterProcessTransportLock(transport):
            message = self.create_message(header, *data)
            with transport:
                self.send_message(transport, message)
                response = self.read_response(transport)
                if len(response) > 0:
                    self.logger.error('Received Unexpected response data: "%s"', repr(response))
    #                raise CommunicationError('Unexpected response data')

    def clear(self, transport):
        with InterProcessTransportLock(transport):
            while True:
                try:
                    transport.read_bytes(25)
                except Timeout:
                    return True
