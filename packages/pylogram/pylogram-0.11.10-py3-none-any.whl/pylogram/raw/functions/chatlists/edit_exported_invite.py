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


class EditExportedInvite(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``653DB63D``

    Parameters:
        chatlist (:obj:`InputChatlist <pylogram.raw.base.InputChatlist>`):
            N/A

        slug (``str``):
            N/A

        title (``str``, *optional*):
            N/A

        peers (List of :obj:`InputPeer <pylogram.raw.base.InputPeer>`, *optional*):
            N/A

    Returns:
        :obj:`ExportedChatlistInvite <pylogram.raw.base.ExportedChatlistInvite>`
    """

    __slots__: List[str] = ["chatlist", "slug", "title", "peers"]

    ID = 0x653db63d
    QUALNAME = "functions.chatlists.EditExportedInvite"

    def __init__(self, *, chatlist: "raw.base.InputChatlist", slug: str, title: Optional[str] = None, peers: Optional[List["raw.base.InputPeer"]] = None) -> None:
        self.chatlist = chatlist  # InputChatlist
        self.slug = slug  # string
        self.title = title  # flags.1?string
        self.peers = peers  # flags.2?Vector<InputPeer>

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "EditExportedInvite":
        
        flags = Int.read(b)
        
        chatlist = TLObject.read(b)
        
        slug = String.read(b)
        
        title = String.read(b) if flags & (1 << 1) else None
        peers = TLObject.read(b) if flags & (1 << 2) else []
        
        return EditExportedInvite(chatlist=chatlist, slug=slug, title=title, peers=peers)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        flags = 0
        flags |= (1 << 1) if self.title is not None else 0
        flags |= (1 << 2) if self.peers else 0
        b.write(Int(flags))
        
        b.write(self.chatlist.write())
        
        b.write(String(self.slug))
        
        if self.title is not None:
            b.write(String(self.title))
        
        if self.peers is not None:
            b.write(Vector(self.peers))
        
        return b.getvalue()
