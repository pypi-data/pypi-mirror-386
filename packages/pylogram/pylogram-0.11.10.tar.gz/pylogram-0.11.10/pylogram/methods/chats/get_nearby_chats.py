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

from typing import List

import pylogram
from pylogram import raw
from pylogram import types
from pylogram import utils


class GetNearbyChats:
    async def get_nearby_chats(
        self: "pylogram.Client",
        latitude: float,
        longitude: float
    ) -> List["types.Chat"]:
        """Get nearby chats.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            latitude (``float``):
                Latitude of the location.

            longitude (``float``):
                Longitude of the location.

        Returns:
            List of :obj:`~pylogram.types.Chat`: On success, a list of nearby chats is returned.

        Example:
            .. code-block:: python

                chats = await app.get_nearby_chats(latitude, longitude)
                print(chats)
        """

        r = await self.invoke(
            raw.functions.contacts.GetLocated(
                geo_point=raw.types.InputGeoPoint(
                    lat=latitude,
                    long=longitude
                )
            )
        )

        if not r.updates:
            return []

        chats = types.List([types.Chat._parse_chat(self, chat) for chat in r.chats])
        peers = r.updates[0].peers

        for peer in peers:
            if isinstance(peer.peer, raw.types.PeerChannel):
                chat_id = utils.get_channel_id(peer.peer.channel_id)

                for chat in chats:
                    if chat.id == chat_id:
                        chat.distance = peer.distance
                        break

        return chats
