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


class EmojiGroup(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.EmojiGroup`.

    Details:
        - Layer: ``181``
        - ID: ``7A9ABDA9``

    Parameters:
        title (``str``):
            N/A

        icon_emoji_id (``int`` ``64-bit``):
            N/A

        emoticons (List of ``str``):
            N/A

    """

    __slots__: List[str] = ["title", "icon_emoji_id", "emoticons"]

    ID = 0x7a9abda9
    QUALNAME = "types.EmojiGroup"

    def __init__(self, *, title: str, icon_emoji_id: int, emoticons: List[str]) -> None:
        self.title = title  # string
        self.icon_emoji_id = icon_emoji_id  # long
        self.emoticons = emoticons  # Vector<string>

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "EmojiGroup":
        # No flags
        
        title = String.read(b)
        
        icon_emoji_id = Long.read(b)
        
        emoticons = TLObject.read(b, String)
        
        return EmojiGroup(title=title, icon_emoji_id=icon_emoji_id, emoticons=emoticons)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(String(self.title))
        
        b.write(Long(self.icon_emoji_id))
        
        b.write(Vector(self.emoticons, String))
        
        return b.getvalue()
