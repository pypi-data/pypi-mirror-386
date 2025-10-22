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
from typing import Union, Optional

import pylogram
from pylogram import raw, utils
from pylogram import types


class SendDice:
    async def send_dice(
        self: "pylogram.Client",
        chat_id: Union[int, str],
        emoji: str = "🎲",
        disable_notification: bool = None,
        reply_to: Union[int, raw.types.InputReplyToMessage, raw.types.InputReplyToStory] = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        reply_markup: Union[
            "types.InlineKeyboardMarkup",
            "types.ReplyKeyboardMarkup",
            "types.ReplyKeyboardRemove",
            "types.ForceReply"
        ] = None
    ) -> Optional["types.Message"]:
        """Send a dice with a random value from 1 to 6.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            emoji (``str``, *optional*):
                Emoji on which the dice throw animation is based.
                Currently, must be one of "🎲", "🎯", "🏀", "⚽", "🎳", or "🎰".
                Dice can have values 1-6 for "🎲", "🎯" and "🎳", values 1-5 for "🏀" and "⚽", and
                values 1-64 for "🎰".
                Defaults to "🎲".

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

            reply_to (``int``, *optional*):
                If the message is a reply, ID of the original message.

            schedule_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the message will be automatically sent.

            protect_content (``bool``, *optional*):
                Protects the contents of the sent message from forwarding and saving.

            reply_markup (:obj:`~pylogram.types.InlineKeyboardMarkup` | :obj:`~pylogram.types.ReplyKeyboardMarkup` | :obj:`~pylogram.types.ReplyKeyboardRemove` | :obj:`~pylogram.types.ForceReply`, *optional*):
                Additional interface options. An object for an inline keyboard, custom reply keyboard,
                instructions to remove reply keyboard or to force a reply from the user.

        Returns:
            :obj:`~pylogram.types.Message`: On success, the sent dice message is returned.

        Example:
            .. code-block:: python

                # Send a dice
                await app.send_dice(chat_id)

                # Send a dart
                await app.send_dice(chat_id, "🎯")

                # Send a basketball
                await app.send_dice(chat_id, "🏀")
        """

        r = await self.invoke(
            raw.functions.messages.SendMedia(
                peer=await self.resolve_peer(chat_id),
                media=raw.types.InputMediaDice(emoticon=emoji),
                silent=disable_notification or None,
                reply_to=raw.types.InputReplyToMessage(
                    reply_to_msg_id=reply_to
                ) if isinstance(reply_to, int) else reply_to,
                random_id=self.rnd_id(),
                schedule_date=utils.datetime_to_timestamp(schedule_date),
                noforwards=protect_content,
                reply_markup=await reply_markup.write(self) if reply_markup else None,
                message=""
            )
        )

        for i in r.updates:
            if isinstance(i, (raw.types.UpdateNewMessage,
                              raw.types.UpdateNewChannelMessage,
                              raw.types.UpdateNewScheduledMessage)):
                return await types.Message._parse(
                    self, i.message,
                    {i.id: i for i in r.users},
                    {i.id: i for i in r.chats},
                    is_scheduled=isinstance(i, raw.types.UpdateNewScheduledMessage)
                )
