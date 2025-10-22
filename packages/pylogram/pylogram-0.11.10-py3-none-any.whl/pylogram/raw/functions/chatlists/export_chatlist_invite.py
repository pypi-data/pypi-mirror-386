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


class ExportChatlistInvite(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``8472478E``

    Parameters:
        chatlist (:obj:`InputChatlist <pylogram.raw.base.InputChatlist>`):
            N/A

        title (``str``):
            N/A

        peers (List of :obj:`InputPeer <pylogram.raw.base.InputPeer>`):
            N/A

    Returns:
        :obj:`chatlists.ExportedChatlistInvite <pylogram.raw.base.chatlists.ExportedChatlistInvite>`
    """

    __slots__: List[str] = ["chatlist", "title", "peers"]

    ID = 0x8472478e
    QUALNAME = "functions.chatlists.ExportChatlistInvite"

    def __init__(self, *, chatlist: "raw.base.InputChatlist", title: str, peers: List["raw.base.InputPeer"]) -> None:
        self.chatlist = chatlist  # InputChatlist
        self.title = title  # string
        self.peers = peers  # Vector<InputPeer>

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "ExportChatlistInvite":
        # No flags
        
        chatlist = TLObject.read(b)
        
        title = String.read(b)
        
        peers = TLObject.read(b)
        
        return ExportChatlistInvite(chatlist=chatlist, title=title, peers=peers)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(self.chatlist.write())
        
        b.write(String(self.title))
        
        b.write(Vector(self.peers))
        
        return b.getvalue()
