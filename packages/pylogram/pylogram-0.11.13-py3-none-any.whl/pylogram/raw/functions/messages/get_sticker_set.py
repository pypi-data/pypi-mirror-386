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


class GetStickerSet(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``C8A0EC74``

    Parameters:
        stickerset (:obj:`InputStickerSet <pylogram.raw.base.InputStickerSet>`):
            N/A

        hash (``int`` ``32-bit``):
            N/A

    Returns:
        :obj:`messages.StickerSet <pylogram.raw.base.messages.StickerSet>`
    """

    __slots__: List[str] = ["stickerset", "hash"]

    ID = 0xc8a0ec74
    QUALNAME = "functions.messages.GetStickerSet"

    def __init__(self, *, stickerset: "raw.base.InputStickerSet", hash: int) -> None:
        self.stickerset = stickerset  # InputStickerSet
        self.hash = hash  # int

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "GetStickerSet":
        # No flags
        
        stickerset = TLObject.read(b)
        
        hash = Int.read(b)
        
        return GetStickerSet(stickerset=stickerset, hash=hash)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(self.stickerset.write())
        
        b.write(Int(self.hash))
        
        return b.getvalue()
