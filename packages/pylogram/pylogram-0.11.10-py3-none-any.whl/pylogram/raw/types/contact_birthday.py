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


class ContactBirthday(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.ContactBirthday`.

    Details:
        - Layer: ``181``
        - ID: ``1D998733``

    Parameters:
        contact_id (``int`` ``64-bit``):
            N/A

        birthday (:obj:`Birthday <pylogram.raw.base.Birthday>`):
            N/A

    """

    __slots__: List[str] = ["contact_id", "birthday"]

    ID = 0x1d998733
    QUALNAME = "types.ContactBirthday"

    def __init__(self, *, contact_id: int, birthday: "raw.base.Birthday") -> None:
        self.contact_id = contact_id  # long
        self.birthday = birthday  # Birthday

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "ContactBirthday":
        # No flags
        
        contact_id = Long.read(b)
        
        birthday = TLObject.read(b)
        
        return ContactBirthday(contact_id=contact_id, birthday=birthday)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Long(self.contact_id))
        
        b.write(self.birthday.write())
        
        return b.getvalue()
