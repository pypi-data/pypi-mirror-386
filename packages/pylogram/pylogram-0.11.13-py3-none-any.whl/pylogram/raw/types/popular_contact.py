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


class PopularContact(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.PopularContact`.

    Details:
        - Layer: ``181``
        - ID: ``5CE14175``

    Parameters:
        client_id (``int`` ``64-bit``):
            N/A

        importers (``int`` ``32-bit``):
            N/A

    """

    __slots__: List[str] = ["client_id", "importers"]

    ID = 0x5ce14175
    QUALNAME = "types.PopularContact"

    def __init__(self, *, client_id: int, importers: int) -> None:
        self.client_id = client_id  # long
        self.importers = importers  # int

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "PopularContact":
        # No flags
        
        client_id = Long.read(b)
        
        importers = Int.read(b)
        
        return PopularContact(client_id=client_id, importers=importers)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Long(self.client_id))
        
        b.write(Int(self.importers))
        
        return b.getvalue()
