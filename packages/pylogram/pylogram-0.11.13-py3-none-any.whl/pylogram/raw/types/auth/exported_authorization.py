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


class ExportedAuthorization(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.auth.ExportedAuthorization`.

    Details:
        - Layer: ``181``
        - ID: ``B434E2B8``

    Parameters:
        id (``int`` ``64-bit``):
            N/A

        bytes (``bytes``):
            N/A

    Functions:
        This object can be returned by 1 function.

        .. currentmodule:: pylogram.raw.functions

        .. autosummary::
            :nosignatures:

            auth.ExportAuthorization
    """

    __slots__: List[str] = ["id", "bytes"]

    ID = 0xb434e2b8
    QUALNAME = "types.auth.ExportedAuthorization"

    def __init__(self, *, id: int, bytes: bytes) -> None:
        self.id = id  # long
        self.bytes = bytes  # bytes

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "ExportedAuthorization":
        # No flags
        
        id = Long.read(b)
        
        bytes = Bytes.read(b)
        
        return ExportedAuthorization(id=id, bytes=bytes)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Long(self.id))
        
        b.write(Bytes(self.bytes))
        
        return b.getvalue()
