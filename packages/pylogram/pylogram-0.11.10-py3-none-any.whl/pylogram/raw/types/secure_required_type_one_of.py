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


class SecureRequiredTypeOneOf(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.SecureRequiredType`.

    Details:
        - Layer: ``181``
        - ID: ``27477B4``

    Parameters:
        types (List of :obj:`SecureRequiredType <pylogram.raw.base.SecureRequiredType>`):
            N/A

    """

    __slots__: List[str] = ["types"]

    ID = 0x27477b4
    QUALNAME = "types.SecureRequiredTypeOneOf"

    def __init__(self, *, types: List["raw.base.SecureRequiredType"]) -> None:
        self.types = types  # Vector<SecureRequiredType>

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "SecureRequiredTypeOneOf":
        # No flags
        
        types = TLObject.read(b)
        
        return SecureRequiredTypeOneOf(types=types)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Vector(self.types))
        
        return b.getvalue()
