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


class ToggleUsername(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``53CA973``

    Parameters:
        bot (:obj:`InputUser <pylogram.raw.base.InputUser>`):
            N/A

        username (``str``):
            N/A

        active (``bool``):
            N/A

    Returns:
        ``bool``
    """

    __slots__: List[str] = ["bot", "username", "active"]

    ID = 0x53ca973
    QUALNAME = "functions.bots.ToggleUsername"

    def __init__(self, *, bot: "raw.base.InputUser", username: str, active: bool) -> None:
        self.bot = bot  # InputUser
        self.username = username  # string
        self.active = active  # Bool

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "ToggleUsername":
        # No flags
        
        bot = TLObject.read(b)
        
        username = String.read(b)
        
        active = Bool.read(b)
        
        return ToggleUsername(bot=bot, username=username, active=active)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(self.bot.write())
        
        b.write(String(self.username))
        
        b.write(Bool(self.active))
        
        return b.getvalue()
