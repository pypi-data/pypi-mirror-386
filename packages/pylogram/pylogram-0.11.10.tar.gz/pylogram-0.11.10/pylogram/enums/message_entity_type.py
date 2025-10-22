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

from pylogram import raw
from .auto_name import AutoName


class MessageEntityType(AutoName):
    """Message entity type enumeration used in :obj:`~pylogram.types.MessageEntity`."""

    MENTION = raw.types.MessageEntityMention
    "``@username``"

    HASHTAG = raw.types.MessageEntityHashtag
    "``#hashtag``"

    CASHTAG = raw.types.MessageEntityCashtag
    "``$USD``"

    BOT_COMMAND = raw.types.MessageEntityBotCommand
    "``/start@pylogrambot``"

    URL = raw.types.MessageEntityUrl
    "``https://example.com`` (see ``url``)"

    EMAIL = raw.types.MessageEntityEmail
    "``do-not-reply@example.com``"

    PHONE_NUMBER = raw.types.MessageEntityPhone
    "``+1-123-456-7890``"

    BOLD = raw.types.MessageEntityBold
    "Bold text"

    ITALIC = raw.types.MessageEntityItalic
    "Italic text"

    UNDERLINE = raw.types.MessageEntityUnderline
    "Underlined text"

    STRIKETHROUGH = raw.types.MessageEntityStrike
    "Strikethrough text"

    SPOILER = raw.types.MessageEntitySpoiler
    "Spoiler text"

    CODE = raw.types.MessageEntityCode
    "Monowidth string"

    PRE = raw.types.MessageEntityPre
    "Monowidth block (see ``language``)"

    BLOCKQUOTE = raw.types.MessageEntityBlockquote
    "Blockquote text"

    TEXT_LINK = raw.types.MessageEntityTextUrl
    "For clickable text URLs"

    TEXT_MENTION = raw.types.MessageEntityMentionName
    "for users without usernames (see ``user``)"

    BANK_CARD = raw.types.MessageEntityBankCard
    "Bank card text"

    CUSTOM_EMOJI = raw.types.MessageEntityCustomEmoji
    "Custom emoji"

    UNKNOWN = raw.types.MessageEntityUnknown
    "Unknown message entity type"
