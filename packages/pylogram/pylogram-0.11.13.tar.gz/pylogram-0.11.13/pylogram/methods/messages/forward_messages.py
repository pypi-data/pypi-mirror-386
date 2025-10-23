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

from datetime import datetime
from typing import Iterable
from typing import List
from typing import Union

import pylogram
from pylogram import raw
from pylogram import types
from pylogram import utils


class ForwardMessages:
    async def forward_messages(
            self: "pylogram.Client",
            chat_id: Union[int, str],
            from_chat_id: Union[int, str],
            message_ids: Union[int, Iterable[int]],
            disable_notification: bool = None,
            schedule_date: datetime = None,
            protect_content: bool = None,
            background: bool = None,
            with_my_score: bool = None,
            drop_author: bool = None,
            drop_media_captions: bool = None,
            send_as: Union[int, str] = None,
            top_msg_id: int | None = None,
    ) -> Union["types.Message", List["types.Message"]]:
        """Forward messages of any kind.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            from_chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the source chat where the original message was sent.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            message_ids (``int`` | Iterable of ``int``):
                An iterable of message identifiers in the chat specified in *from_chat_id* or a single message id.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            background (``bool``, *optional*):
                Whether to send the message in background.

            with_my_score (``bool``, *optional*):
                When forwarding games, whether to include your score in the game.

            drop_author (``bool``, *optional*):
                Whether to forward messages without quoting the original author.

            drop_media_captions (``bool``, *optional*):
                Whether to strip captions from media.

            send_as (``int`` | ``str``, *optional*):
                Forward the messages as the specified user or chat.

            top_msg_id (``int`` | ``str``, *optional*):
                Forward the messages to specified topic id of forum.

        Returns:
            :obj:`~pylogram.types.Message` | List of :obj:`~pylogram.types.Message`: In case *message_ids* was not
            a list, a single message is returned, otherwise a list of messages is returned.

        Example:
            .. code-block:: python

                # Forward a single message
                await app.forward_messages(to_chat, from_chat, 123)

                # Forward multiple messages at once
                await app.forward_messages(to_chat, from_chat, [1, 2, 3])
        """

        is_iterable = not isinstance(message_ids, int)
        message_ids = list(message_ids) if is_iterable else [message_ids]

        if bool(send_as):
            send_as = await self.resolve_peer(send_as)

        r = await self.invoke(
            raw.functions.messages.ForwardMessages(
                to_peer=await self.resolve_peer(chat_id),
                from_peer=await self.resolve_peer(from_chat_id),
                id=message_ids,
                silent=disable_notification or None,
                random_id=[self.rnd_id() for _ in message_ids],
                schedule_date=utils.datetime_to_timestamp(schedule_date),
                noforwards=protect_content,
                background=background,
                with_my_score=with_my_score,
                drop_author=drop_author,
                drop_media_captions=drop_media_captions,
                send_as=send_as,
                top_msg_id=top_msg_id
            )
        )

        forwarded_messages = []

        users = {i.id: i for i in r.users}
        chats = {i.id: i for i in r.chats}

        for i in r.updates:
            if isinstance(i, (raw.types.UpdateNewMessage,
                              raw.types.UpdateNewChannelMessage,
                              raw.types.UpdateNewScheduledMessage)):
                forwarded_messages.append(
                    await types.Message._parse(
                        self, i.message,
                        users, chats
                    )
                )

        return types.List(forwarded_messages) if is_iterable else forwarded_messages[0]
