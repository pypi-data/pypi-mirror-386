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


class InvokeAfterMsgs(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``3DC4B4F0``

    Parameters:
        msg_ids (List of ``int`` ``64-bit``):
            N/A

        query (Any function from :obj:`~pylogram.raw.functions`):
            N/A

    Returns:
        Any object from :obj:`~pylogram.raw.types`
    """

    __slots__: List[str] = ["msg_ids", "query"]

    ID = 0x3dc4b4f0
    QUALNAME = "functions.InvokeAfterMsgs"

    def __init__(self, *, msg_ids: List[int], query: TLObject) -> None:
        self.msg_ids = msg_ids  # Vector<long>
        self.query = query  # !X

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "InvokeAfterMsgs":
        # No flags
        
        msg_ids = TLObject.read(b, Long)
        
        query = TLObject.read(b)
        
        return InvokeAfterMsgs(msg_ids=msg_ids, query=query)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Vector(self.msg_ids, Long))
        
        b.write(self.query.write())
        
        return b.getvalue()
