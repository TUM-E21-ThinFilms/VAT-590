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

import logging

from slave.transport import Serial
from protocol import VAT590Protocol
from driver import VAT590Driver


class VAT590Factory:
    def get_logger(self):
        logger = logging.getLogger('VAT 590 Series')
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler('vat590.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    def create_valve(self, device='/dev/ttyUSB5', logger=None):
        if logger is None:
            logger = self.get_logger()

        protocol = VAT590Protocol(logger=logger)
        return VAT590Driver(Serial(device, 9600, 7, 'E', 1, 0.2), protocol)

