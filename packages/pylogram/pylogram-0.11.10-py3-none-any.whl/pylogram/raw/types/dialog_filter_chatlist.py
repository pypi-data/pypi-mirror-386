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


class DialogFilterChatlist(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.DialogFilter`.

    Details:
        - Layer: ``181``
        - ID: ``9FE28EA4``

    Parameters:
        id (``int`` ``32-bit``):
            N/A

        title (``str``):
            N/A

        pinned_peers (List of :obj:`InputPeer <pylogram.raw.base.InputPeer>`):
            N/A

        include_peers (List of :obj:`InputPeer <pylogram.raw.base.InputPeer>`):
            N/A

        has_my_invites (``bool``, *optional*):
            N/A

        emoticon (``str``, *optional*):
            N/A

        color (``int`` ``32-bit``, *optional*):
            N/A

    """

    __slots__: List[str] = ["id", "title", "pinned_peers", "include_peers", "has_my_invites", "emoticon", "color"]

    ID = 0x9fe28ea4
    QUALNAME = "types.DialogFilterChatlist"

    def __init__(self, *, id: int, title: str, pinned_peers: List["raw.base.InputPeer"], include_peers: List["raw.base.InputPeer"], has_my_invites: Optional[bool] = None, emoticon: Optional[str] = None, color: Optional[int] = None) -> None:
        self.id = id  # int
        self.title = title  # string
        self.pinned_peers = pinned_peers  # Vector<InputPeer>
        self.include_peers = include_peers  # Vector<InputPeer>
        self.has_my_invites = has_my_invites  # flags.26?true
        self.emoticon = emoticon  # flags.25?string
        self.color = color  # flags.27?int

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "DialogFilterChatlist":
        
        flags = Int.read(b)
        
        has_my_invites = True if flags & (1 << 26) else False
        id = Int.read(b)
        
        title = String.read(b)
        
        emoticon = String.read(b) if flags & (1 << 25) else None
        color = Int.read(b) if flags & (1 << 27) else None
        pinned_peers = TLObject.read(b)
        
        include_peers = TLObject.read(b)
        
        return DialogFilterChatlist(id=id, title=title, pinned_peers=pinned_peers, include_peers=include_peers, has_my_invites=has_my_invites, emoticon=emoticon, color=color)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        flags = 0
        flags |= (1 << 26) if self.has_my_invites else 0
        flags |= (1 << 25) if self.emoticon is not None else 0
        flags |= (1 << 27) if self.color is not None else 0
        b.write(Int(flags))
        
        b.write(Int(self.id))
        
        b.write(String(self.title))
        
        if self.emoticon is not None:
            b.write(String(self.emoticon))
        
        if self.color is not None:
            b.write(Int(self.color))
        
        b.write(Vector(self.pinned_peers))
        
        b.write(Vector(self.include_peers))
        
        return b.getvalue()
