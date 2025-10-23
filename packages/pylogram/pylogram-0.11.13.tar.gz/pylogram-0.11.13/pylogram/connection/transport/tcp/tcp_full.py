#  Pylogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-2024 Pylakey <https://github.com/pylakey>
#
#  This file is part of Pylogram.
#
#  Pylogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pylogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pylogram.  If not, see <http://www.gnu.org/licenses/>.

import logging
from binascii import crc32
from struct import pack
from struct import unpack
from typing import Optional

from .tcp import TCP

log = logging.getLogger(__name__)


class TCPFull(TCP):
    def __init__(self, ipv6: bool, proxy: dict):
        super().__init__(ipv6, proxy)
        self.seq_no = 0

    async def connect(self, address: tuple):
        await super().connect(address)
        self.seq_no = 0

    async def send(self, data: bytes, *args):
        length = len(data) + 12
        data = pack('<ii', length, self.seq_no) + data
        crc = pack('<I', crc32(data))
        data = data + crc
        # data = pack("<II", len(data) + 12, self.seq_no) + data
        # data += pack("<I", crc32(data))
        self.seq_no += 1

        await super().send(data)

    async def recv(self, length: int = 0) -> Optional[bytes]:
        length = await super().recv(4)

        if length is None:
            return None

        packet = await super().recv(unpack("<I", length)[0] - 4)

        if packet is None:
            return None

        packet = length + packet
        checksum = packet[-4:]
        packet = packet[:-4]

        if crc32(packet) != unpack("<I", checksum)[0]:
            return None

        return packet[8:]
