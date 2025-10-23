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


class EditBusinessChatLink(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``8C3410AF``

    Parameters:
        slug (``str``):
            N/A

        link (:obj:`InputBusinessChatLink <pylogram.raw.base.InputBusinessChatLink>`):
            N/A

    Returns:
        :obj:`BusinessChatLink <pylogram.raw.base.BusinessChatLink>`
    """

    __slots__: List[str] = ["slug", "link"]

    ID = 0x8c3410af
    QUALNAME = "functions.account.EditBusinessChatLink"

    def __init__(self, *, slug: str, link: "raw.base.InputBusinessChatLink") -> None:
        self.slug = slug  # string
        self.link = link  # InputBusinessChatLink

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "EditBusinessChatLink":
        # No flags
        
        slug = String.read(b)
        
        link = TLObject.read(b)
        
        return EditBusinessChatLink(slug=slug, link=link)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(String(self.slug))
        
        b.write(self.link.write())
        
        return b.getvalue()
