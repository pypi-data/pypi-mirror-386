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


class GetCustomEmojiStickers:
    async def get_custom_emoji_stickers(
        self: "pylogram.Client",
        custom_emoji_ids: List[int],
    ) -> List["types.Sticker"]:
        """Get information about custom emoji stickers by their identifiers.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            custom_emoji_ids (List of ``int``):
                List of custom emoji identifiers.
                At most 200 custom emoji identifiers can be specified.

        Returns:
            List of :obj:`~pylogram.types.Sticker`: On success, a list of sticker objects is returned.
        """
        result = await self.invoke(
            raw.functions.messages.GetCustomEmojiDocuments(
                document_id=custom_emoji_ids
            )
        )

        stickers = []
        for item in result:
            attributes = {type(i): i for i in item.attributes}
            sticker = await types.Sticker._parse(self, item, attributes)
            stickers.append(sticker)

        return pylogram.types.List(stickers)
