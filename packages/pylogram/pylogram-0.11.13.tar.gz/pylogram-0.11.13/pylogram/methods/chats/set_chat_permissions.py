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

from typing import Union

import pylogram
from pylogram import raw
from pylogram import types


class SetChatPermissions:
    async def set_chat_permissions(
        self: "pylogram.Client",
        chat_id: Union[int, str],
        permissions: "types.ChatPermissions",
    ) -> "types.Chat":
        """Set default chat permissions for all members.

        You must be an administrator in the group or a supergroup for this to work and must have the
        *can_restrict_members* admin rights.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            permissions (:obj:`~pylogram.types.ChatPermissions`):
                New default chat permissions.

        Returns:
            :obj:`~pylogram.types.Chat`: On success, a chat object is returned.

        Example:
            .. code-block:: python

                from pylogram.types import ChatPermissions

                # Completely restrict chat
                await app.set_chat_permissions(chat_id, ChatPermissions())

                # Chat members can only send text messages and media messages
                await app.set_chat_permissions(
                    chat_id,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True
                    )
                )
        """

        r = await self.invoke(
            raw.functions.messages.EditChatDefaultBannedRights(
                peer=await self.resolve_peer(chat_id),
                banned_rights=raw.types.ChatBannedRights(
                    until_date=0,
                    view_messages=not permissions.can_view_messages,
                    send_messages=not permissions.can_send_messages,
                    send_media=not permissions.can_send_media,
                    send_stickers=not permissions.can_send_stickers,
                    send_gifs=not permissions.can_send_gifs,
                    send_games=not permissions.can_send_games,
                    send_inline=not permissions.can_send_inline,
                    embed_links=not permissions.can_embed_links,
                    send_polls=not permissions.can_send_polls,
                    change_info=not permissions.can_change_info,
                    invite_users=not permissions.can_invite_users,
                    pin_messages=not permissions.can_pin_messages,
                    manage_topics=not permissions.can_manage_topics,
                    send_photos=not permissions.can_send_photos,
                    send_videos=not permissions.can_send_videos,
                    send_roundvideos=not permissions.can_send_roundvideos,
                    send_audios=not permissions.can_send_audios,
                    send_voices=not permissions.can_send_voices,
                    send_docs=not permissions.can_send_docs,
                    send_plain=not permissions.can_send_plain,
                )
            )
        )

        return types.Chat._parse_chat(self, r.chats[0])
