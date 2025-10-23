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


class SendEncrypted(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``44FA7A15``

    Parameters:
        peer (:obj:`InputEncryptedChat <pylogram.raw.base.InputEncryptedChat>`):
            N/A

        random_id (``int`` ``64-bit``):
            N/A

        data (``bytes``):
            N/A

        silent (``bool``, *optional*):
            N/A

    Returns:
        :obj:`messages.SentEncryptedMessage <pylogram.raw.base.messages.SentEncryptedMessage>`
    """

    __slots__: List[str] = ["peer", "random_id", "data", "silent"]

    ID = 0x44fa7a15
    QUALNAME = "functions.messages.SendEncrypted"

    def __init__(self, *, peer: "raw.base.InputEncryptedChat", random_id: int, data: bytes, silent: Optional[bool] = None) -> None:
        self.peer = peer  # InputEncryptedChat
        self.random_id = random_id  # long
        self.data = data  # bytes
        self.silent = silent  # flags.0?true

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "SendEncrypted":
        
        flags = Int.read(b)
        
        silent = True if flags & (1 << 0) else False
        peer = TLObject.read(b)
        
        random_id = Long.read(b)
        
        data = Bytes.read(b)
        
        return SendEncrypted(peer=peer, random_id=random_id, data=data, silent=silent)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        flags = 0
        flags |= (1 << 0) if self.silent else 0
        b.write(Int(flags))
        
        b.write(self.peer.write())
        
        b.write(Long(self.random_id))
        
        b.write(Bytes(self.data))
        
        return b.getvalue()
