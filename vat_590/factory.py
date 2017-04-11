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

from e21_util.transport import Serial
from e21_util.logging import get_sputter_logger
from protocol import VAT590Protocol
from driver import VAT590Driver

class VAT590Factory:
    def get_logger(self, type):
        return get_sputter_logger('VAT 590 Series - '+ str(type), 'vat590.log')

    def create_argon_valve(self, device='/dev/ttyUSB5', logger=None):
        if logger is None:
            logger = self.get_logger('argon')

        protocol = VAT590Protocol(logger=logger)
        return VAT590Driver(Serial(device, 9600, 7, 'E', 1, 0.2), protocol)

    def create_oxygen_valve(self, device='/dev/ttyUSB6', logger=None):
        if logger is None:
            logger = self.get_logger('oxygen')

        protocol = VAT590Protocol(logger=logger)
        return VAT590Driver(Serial(device, 9600, 7, 'E', 1, 0.2), protocol)
