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


class SentEncryptedMessage(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.messages.SentEncryptedMessage`.

    Details:
        - Layer: ``181``
        - ID: ``560F8935``

    Parameters:
        date (``int`` ``32-bit``):
            N/A

    Functions:
        This object can be returned by 3 functions.

        .. currentmodule:: pylogram.raw.functions

        .. autosummary::
            :nosignatures:

            messages.SendEncrypted
            messages.SendEncryptedFile
            messages.SendEncryptedService
    """

    __slots__: List[str] = ["date"]

    ID = 0x560f8935
    QUALNAME = "types.messages.SentEncryptedMessage"

    def __init__(self, *, date: int) -> None:
        self.date = date  # int

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "SentEncryptedMessage":
        # No flags
        
        date = Int.read(b)
        
        return SentEncryptedMessage(date=date)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Int(self.date))
        
        return b.getvalue()
