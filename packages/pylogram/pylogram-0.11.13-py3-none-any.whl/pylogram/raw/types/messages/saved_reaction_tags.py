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


class SavedReactionTags(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.messages.SavedReactionTags`.

    Details:
        - Layer: ``181``
        - ID: ``3259950A``

    Parameters:
        tags (List of :obj:`SavedReactionTag <pylogram.raw.base.SavedReactionTag>`):
            N/A

        hash (``int`` ``64-bit``):
            N/A

    Functions:
        This object can be returned by 1 function.

        .. currentmodule:: pylogram.raw.functions

        .. autosummary::
            :nosignatures:

            messages.GetSavedReactionTags
    """

    __slots__: List[str] = ["tags", "hash"]

    ID = 0x3259950a
    QUALNAME = "types.messages.SavedReactionTags"

    def __init__(self, *, tags: List["raw.base.SavedReactionTag"], hash: int) -> None:
        self.tags = tags  # Vector<SavedReactionTag>
        self.hash = hash  # long

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "SavedReactionTags":
        # No flags
        
        tags = TLObject.read(b)
        
        hash = Long.read(b)
        
        return SavedReactionTags(tags=tags, hash=hash)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Vector(self.tags))
        
        b.write(Long(self.hash))
        
        return b.getvalue()
