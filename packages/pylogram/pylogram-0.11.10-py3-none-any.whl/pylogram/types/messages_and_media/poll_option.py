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

import pylogram
from ..object import Object


class PollOption(Object):
    """Contains information about one answer option in a poll.

    Parameters:
        text (``str``):
            Option text, 1-100 characters.

        voter_count (``int``):
            Number of users that voted for this option.
            Equals to 0 until you vote.

        data (``bytes``):
            The data this poll option is holding.
    """

    def __init__(
        self,
        *,
        client: "pylogram.Client" = None,
        text: str,
        voter_count: int,
        data: bytes
    ):
        super().__init__(client)

        self.text = text
        self.voter_count = voter_count
        self.data = data
