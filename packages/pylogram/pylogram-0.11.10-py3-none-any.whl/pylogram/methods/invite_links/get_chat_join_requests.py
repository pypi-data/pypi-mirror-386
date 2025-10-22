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

from typing import Union, Optional, AsyncGenerator

import pylogram
from pylogram import raw
from pylogram import types


class GetChatJoinRequests:
    async def get_chat_join_requests(
        self: "pylogram.Client",
        chat_id: Union[int, str],
        limit: int = 0,
        query: str = ""
    ) -> Optional[AsyncGenerator["types.ChatJoiner", None]]:
        """Get the pending join requests of a chat.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier for the target chat or username of the target channel/supergroup
                (in the format @username).

            limit (``int``, *optional*):
                Limits the number of invite links to be retrieved.
                By default, no limit is applied and all invite links are returned.

            query (``str``, *optional*):
                Query to search for a user.

        Returns:
            ``Generator``: A generator yielding :obj:`~pylogram.types.ChatJoiner` objects.

        Yields:
            :obj:`~pylogram.types.ChatJoiner` objects.
        """
        current = 0
        total = abs(limit) or (1 << 31) - 1
        limit = min(100, total)

        offset_date = 0
        offset_user = raw.types.InputUserEmpty()

        while True:
            r = await self.invoke(
                raw.functions.messages.GetChatInviteImporters(
                    peer=await self.resolve_peer(chat_id),
                    limit=limit,
                    offset_date=offset_date,
                    offset_user=offset_user,
                    requested=True,
                    q=query
                )
            )

            if not r.importers:
                break

            users = {i.id: i for i in r.users}

            offset_date = r.importers[-1].date
            offset_user = await self.resolve_peer(r.importers[-1].user_id)

            for i in r.importers:
                yield types.ChatJoiner._parse(self, i, users)

                current += 1

                if current >= total:
                    return
