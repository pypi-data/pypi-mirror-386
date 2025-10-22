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


class BroadcastRevenueTransactionProceeds(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.BroadcastRevenueTransaction`.

    Details:
        - Layer: ``181``
        - ID: ``557E2CC4``

    Parameters:
        amount (``int`` ``64-bit``):
            N/A

        from_date (``int`` ``32-bit``):
            N/A

        to_date (``int`` ``32-bit``):
            N/A

    """

    __slots__: List[str] = ["amount", "from_date", "to_date"]

    ID = 0x557e2cc4
    QUALNAME = "types.BroadcastRevenueTransactionProceeds"

    def __init__(self, *, amount: int, from_date: int, to_date: int) -> None:
        self.amount = amount  # long
        self.from_date = from_date  # int
        self.to_date = to_date  # int

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "BroadcastRevenueTransactionProceeds":
        # No flags
        
        amount = Long.read(b)
        
        from_date = Int.read(b)
        
        to_date = Int.read(b)
        
        return BroadcastRevenueTransactionProceeds(amount=amount, from_date=from_date, to_date=to_date)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        # No flags
        
        b.write(Long(self.amount))
        
        b.write(Int(self.from_date))
        
        b.write(Int(self.to_date))
        
        return b.getvalue()
