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

import os
import re
from datetime import datetime
from typing import Union, BinaryIO, List, Optional, Callable

import pylogram
from pylogram import enums
from pylogram import typevars
from pylogram.errors.lib_errors import StopTransmission
from pylogram import raw
from pylogram import types
from pylogram import utils
from pylogram.errors import FilePartMissing
from pylogram.file_id import FileType


class SendAudio:
    async def send_audio(
        self: "pylogram.Client",
        chat_id: Union[int, str],
        audio: Union[str, BinaryIO],
        caption: str = "",
        parse_mode: Optional["enums.ParseMode"] = None,
        caption_entities: List["types.MessageEntity"] = None,
        duration: int = 0,
        performer: str = None,
        title: str = None,
        thumb: Union[str, BinaryIO] = None,
        file_name: str = None,
        disable_notification: bool = None,
        reply_to: Union[int, raw.types.InputReplyToMessage, raw.types.InputReplyToStory] = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        reply_markup: Union[
            "types.InlineKeyboardMarkup",
            "types.ReplyKeyboardMarkup",
            "types.ReplyKeyboardRemove",
            "types.ForceReply"
        ] = None,
        progress: typevars.ProgressCallable = None,
        progress_args: tuple = ()
    ) -> Optional["types.Message"]:
        """Send audio files.

        For sending voice messages, use the :meth:`~pylogram.Client.send_voice` method instead.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            audio (``str`` | ``BinaryIO``):
                Audio file to send.
                Pass a file_id as string to send an audio file that exists on the Telegram servers,
                pass an HTTP URL as a string for Telegram to get an audio file from the Internet,
                pass a file path as string to upload a new audio file that exists on your local machine, or
                pass a binary file-like object with its attribute ".name" set for in-memory uploads.

            caption (``str``, *optional*):
                Audio caption, 0-1024 characters.

            parse_mode (:obj:`~pylogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            caption_entities (List of :obj:`~pylogram.types.MessageEntity`):
                List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

            duration (``int``, *optional*):
                Duration of the audio in seconds.

            performer (``str``, *optional*):
                Performer.

            title (``str``, *optional*):
                Track name.

            thumb (``str`` | ``BinaryIO``, *optional*):
                Thumbnail of the music file album cover.
                The thumbnail should be in JPEG format and less than 200 KB in size.
                A thumbnail's width and height should not exceed 320 pixels.
                Thumbnails can't be reused and can be only uploaded as a new file.

            file_name (``str``, *optional*):
                File name of the audio sent.
                Defaults to file's path basename.

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

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            :obj:`~pylogram.types.Message` | ``None``: On success, the sent audio message is returned, otherwise, in
            case the upload is deliberately stopped with :meth:`~pylogram.Client.stop_transmission`, None is returned.

        Example:
            .. code-block:: python

                # Send audio file by uploading from file
                await app.send_audio("me", "audio.mp3")

                # Add caption to the audio
                await app.send_audio("me", "audio.mp3", caption="audio caption")

                # Set audio metadata
                await app.send_audio(
                    "me", "audio.mp3",
                    title="Title", performer="Performer", duration=234)

                # Keep track of the progress while uploading
                async def progress(current, total):
                    print(f"{current * 100 / total:.1f}%")

                await app.send_audio("me", "audio.mp3", progress=progress)
        """
        file = None

        try:
            if isinstance(audio, str):
                if os.path.isfile(audio):
                    thumb = await self.save_file(thumb)
                    file = await self.save_file(audio, progress=progress, progress_args=progress_args)
                    media = raw.types.InputMediaUploadedDocument(
                        mime_type=self.guess_mime_type(audio) or "audio/mpeg",
                        file=file,
                        thumb=thumb,
                        attributes=[
                            raw.types.DocumentAttributeAudio(
                                duration=duration,
                                performer=performer,
                                title=title
                            ),
                            raw.types.DocumentAttributeFilename(file_name=file_name or os.path.basename(audio))
                        ]
                    )
                elif re.match("^https?://", audio):
                    media = raw.types.InputMediaDocumentExternal(
                        url=audio
                    )
                else:
                    media = utils.get_input_media_from_file_id(audio, FileType.AUDIO)
            else:
                thumb = await self.save_file(thumb)
                file = await self.save_file(audio, progress=progress, progress_args=progress_args)
                media = raw.types.InputMediaUploadedDocument(
                    mime_type=self.guess_mime_type(file_name or audio.name) or "audio/mpeg",
                    file=file,
                    thumb=thumb,
                    attributes=[
                        raw.types.DocumentAttributeAudio(
                            duration=duration,
                            performer=performer,
                            title=title
                        ),
                        raw.types.DocumentAttributeFilename(file_name=file_name or audio.name)
                    ]
                )

            while True:
                try:
                    r = await self.invoke(
                        raw.functions.messages.SendMedia(
                            peer=await self.resolve_peer(chat_id),
                            media=media,
                            silent=disable_notification or None,
                            reply_to=raw.types.InputReplyToMessage(
                                reply_to_msg_id=reply_to
                            ) if isinstance(reply_to, int) else reply_to,
                            random_id=self.rnd_id(),
                            schedule_date=utils.datetime_to_timestamp(schedule_date),
                            noforwards=protect_content,
                            reply_markup=await reply_markup.write(self) if reply_markup else None,
                            **await utils.parse_text_entities(self, caption, parse_mode, caption_entities)
                        )
                    )
                except FilePartMissing as e:
                    await self.save_file(audio, file_id=file.id, file_part=e.value)
                else:
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
        except StopTransmission:
            return None
