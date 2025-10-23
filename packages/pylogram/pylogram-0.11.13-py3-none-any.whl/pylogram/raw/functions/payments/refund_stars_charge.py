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


class RefundStarsCharge(TLObject):  # type: ignore
    """Telegram API function.

    Details:
        - Layer: ``181``
        - ID: ``25AE8F4A``

    Parameters:
        user_id (:obj:`InputUser <pylogram.raw.base.InputUser>`):
            N/A

        charge_id (``str``):
            N/A

    Returns:
        :obj:`Updates <pylogram.raw.base.Updates>`
    """

    __slots__: List[str] = ["user_id", "charge_id"]

    ID = 0x25ae8f4a
    QUALNAME = "functions.payments.RefundStarsCharge"

    def __init__(self, *, user_id: "raw.base.InputUser", charge_id: str) -> None:
        self.user_id = user_id  # InputUser
        self.charge_id = charge_id  # string

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "RefundStarsCharge":
        # No flags
        
        user_id = TLObject.read(b)
        
        charge_id = String.read(b)
        
        return RefundStarsCharge(user_id=user_id, charge_id=charge_id)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(self.user_id.write())
        
        b.write(String(self.charge_id))
        
        return b.getvalue()
