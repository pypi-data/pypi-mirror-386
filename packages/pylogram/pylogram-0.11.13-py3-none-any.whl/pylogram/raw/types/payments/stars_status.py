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


class StarsStatus(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.payments.StarsStatus`.

    Details:
        - Layer: ``181``
        - ID: ``8CF4EE60``

    Parameters:
        balance (``int`` ``64-bit``):
            N/A

        history (List of :obj:`StarsTransaction <pylogram.raw.base.StarsTransaction>`):
            N/A

        chats (List of :obj:`Chat <pylogram.raw.base.Chat>`):
            N/A

        users (List of :obj:`User <pylogram.raw.base.User>`):
            N/A

        next_offset (``str``, *optional*):
            N/A

    Functions:
        This object can be returned by 2 functions.

        .. currentmodule:: pylogram.raw.functions

        .. autosummary::
            :nosignatures:

            payments.GetStarsStatus
            payments.GetStarsTransactions
    """

    __slots__: List[str] = ["balance", "history", "chats", "users", "next_offset"]

    ID = 0x8cf4ee60
    QUALNAME = "types.payments.StarsStatus"

    def __init__(self, *, balance: int, history: List["raw.base.StarsTransaction"], chats: List["raw.base.Chat"], users: List["raw.base.User"], next_offset: Optional[str] = None) -> None:
        self.balance = balance  # long
        self.history = history  # Vector<StarsTransaction>
        self.chats = chats  # Vector<Chat>
        self.users = users  # Vector<User>
        self.next_offset = next_offset  # flags.0?string

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "StarsStatus":
        
        flags = Int.read(b)
        
        balance = Long.read(b)
        
        history = TLObject.read(b)
        
        next_offset = String.read(b) if flags & (1 << 0) else None
        chats = TLObject.read(b)
        
        users = TLObject.read(b)
        
        return StarsStatus(balance=balance, history=history, chats=chats, users=users, next_offset=next_offset)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        flags = 0
        flags |= (1 << 0) if self.next_offset is not None else 0
        b.write(Int(flags))
        
        b.write(Long(self.balance))
        
        b.write(Vector(self.history))
        
        if self.next_offset is not None:
            b.write(String(self.next_offset))
        
        b.write(Vector(self.chats))
        
        b.write(Vector(self.users))
        
        return b.getvalue()
