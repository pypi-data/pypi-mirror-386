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


class SetBlocked(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``94C65C76``

    Parameters:
        id (List of :obj:`InputPeer <pylogram.raw.base.InputPeer>`):
            N/A

        limit (``int`` ``32-bit``):
            N/A

        my_stories_from (``bool``, *optional*):
            N/A

    Returns:
        ``bool``
    """

    __slots__: List[str] = ["id", "limit", "my_stories_from"]

    ID = 0x94c65c76
    QUALNAME = "functions.contacts.SetBlocked"

    def __init__(self, *, id: List["raw.base.InputPeer"], limit: int, my_stories_from: Optional[bool] = None) -> None:
        self.id = id  # Vector<InputPeer>
        self.limit = limit  # int
        self.my_stories_from = my_stories_from  # flags.0?true

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "SetBlocked":
        
        flags = Int.read(b)
        
        my_stories_from = True if flags & (1 << 0) else False
        id = TLObject.read(b)
        
        limit = Int.read(b)
        
        return SetBlocked(id=id, limit=limit, my_stories_from=my_stories_from)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        flags = 0
        flags |= (1 << 0) if self.my_stories_from else 0
        b.write(Int(flags))
        
        b.write(Vector(self.id))
        
        b.write(Int(self.limit))
        
        return b.getvalue()
