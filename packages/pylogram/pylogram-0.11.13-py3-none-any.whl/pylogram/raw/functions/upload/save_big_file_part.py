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

from io import BytesIO

from pylogram.raw.core.primitives import Int, Long, Int128, Int256, Bool, Bytes, String, Double, Vector
from pylogram.raw.core import TLObject
from pylogram import raw
from typing import List, Optional, Any

# # # # # # # # # # # # # # # # # # # # # # # #
#               !!! WARNING !!!               #
#          This is a generated file!          #
# All changes made in this file will be lost! #
# # # # # # # # # # # # # # # # # # # # # # # #


class SaveBigFilePart(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``DE7B673D``

    Parameters:
        file_id (``int`` ``64-bit``):
            N/A

        file_part (``int`` ``32-bit``):
            N/A

        file_total_parts (``int`` ``32-bit``):
            N/A

        bytes (``bytes``):
            N/A

    Returns:
        ``bool``
    """

    __slots__: List[str] = ["file_id", "file_part", "file_total_parts", "bytes"]

    ID = 0xde7b673d
    QUALNAME = "functions.upload.SaveBigFilePart"

    def __init__(self, *, file_id: int, file_part: int, file_total_parts: int, bytes: bytes) -> None:
        self.file_id = file_id  # long
        self.file_part = file_part  # int
        self.file_total_parts = file_total_parts  # int
        self.bytes = bytes  # bytes

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "SaveBigFilePart":
        # No flags
        
        file_id = Long.read(b)
        
        file_part = Int.read(b)
        
        file_total_parts = Int.read(b)
        
        bytes = Bytes.read(b)
        
        return SaveBigFilePart(file_id=file_id, file_part=file_part, file_total_parts=file_total_parts, bytes=bytes)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Long(self.file_id))
        
        b.write(Int(self.file_part))
        
        b.write(Int(self.file_total_parts))
        
        b.write(Bytes(self.bytes))
        
        return b.getvalue()
