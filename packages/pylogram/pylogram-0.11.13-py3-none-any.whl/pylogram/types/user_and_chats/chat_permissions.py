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
from warnings import warn

from pylogram import raw
from ..object import Object


class ChatPermissions(Object):
    """Describes actions that a non-administrator user is allowed to take in a chat.

    Parameters:
        can_view_messages (``bool``, *optional*):
            True, if the user is allowed to view messages.

        can_send_messages (``bool``, *optional*):
            True, if the user is allowed to send text messages, contacts, locations and venues.

        can_send_messages (``bool``, *optional*):
            True, if the user is allowed to send messages

        can_send_media (``bool``, *optional*):
            True, if the user is allowed to send any media

        can_send_stickers (``bool``, *optional*):
            True, if the user is allowed to send stickers

        can_send_gifs (``bool``, *optional*):
            True, if the user is allowed to send gifs

        can_send_games (``bool``, *optional*):
            True, if the user is allowed to send games

        can_send_inline (``bool``, *optional*):
            True, if the user is allowed to use inline bots

        can_embed_links (``bool``, *optional*):
            True, if the user is allowed to embed links in the messages

        can_send_polls (``bool``, *optional*):
            True, if the user is allowed to send polls

        can_change_info (``bool``, *optional*):
            True, if the user is allowed to change the description of a supergroup/chat

        can_invite_users (``bool``, *optional*):
            True, if the user is allowed to invite users

        can_pin_messages (``bool``, *optional*):
            True, if the user is allowed to pin messages

        can_manage_topics (``bool``, *optional*):
            True, if the user is allowed to create, delete or modify forum topics

        can_send_photos (``bool``, *optional*):
            True, if the user is allowed to send photos

        can_send_videos (``bool``, *optional*):
            True, if the user is allowed to send videos

        can_send_roundvideos (``bool``, *optional*):
            True, if the user is allowed to send round videos

        can_send_audios (``bool``, *optional*):
            True, if the user is allowed to send audio files

        can_send_voices (``bool``, *optional*):
            True, if the user is allowed to send voice messages

        can_send_docs (``bool``, *optional*):
            True, if the user is allowed to send documents

        can_send_plain (``bool``, *optional*):
            True, if the user is allowed to send text messages

    """

    def __init__(
            self,
            *,
            can_view_messages: bool = None,
            can_send_messages: bool = None,
            can_send_media: bool = None,
            can_send_stickers: bool = None,
            can_send_gifs: bool = None,
            can_send_games: bool = None,
            can_send_inline: bool = None,
            can_embed_links: bool = None,
            can_send_polls: bool = None,
            can_change_info: bool = None,
            can_invite_users: bool = None,
            can_pin_messages: bool = None,
            can_manage_topics: bool = None,
            can_send_photos: bool = None,
            can_send_videos: bool = None,
            can_send_roundvideos: bool = None,
            can_send_audios: bool = None,
            can_send_voices: bool = None,
            can_send_docs: bool = None,
            can_send_plain: bool = None,
    ):
        super().__init__(None)
        self.can_send_messages = can_send_messages
        self.can_send_media = can_send_media
        self.can_send_stickers = can_send_stickers
        self.can_send_gifs = can_send_gifs
        self.can_send_games = can_send_games
        self.can_send_inline = can_send_inline
        self.can_send_polls = can_send_polls
        self.can_send_photos = can_send_photos
        self.can_send_videos = can_send_videos
        self.can_send_roundvideos = can_send_roundvideos
        self.can_send_audios = can_send_audios
        self.can_send_voices = can_send_voices
        self.can_send_docs = can_send_docs
        self.can_send_plain = can_send_plain
        self.can_view_messages = can_view_messages
        self.can_embed_links = can_embed_links
        self.can_manage_topics = can_manage_topics
        self.can_change_info = can_change_info
        self.can_invite_users = can_invite_users
        self.can_pin_messages = can_pin_messages

    @staticmethod
    def _parse(denied_permissions: "raw.base.ChatBannedRights") -> "ChatPermissions":
        if isinstance(denied_permissions, raw.types.ChatBannedRights):
            return ChatPermissions(
                can_view_messages=not denied_permissions.view_messages,
                can_send_messages=not denied_permissions.send_messages,
                can_send_media=not denied_permissions.send_media,
                can_send_stickers=not denied_permissions.send_stickers,
                can_send_gifs=not denied_permissions.send_gifs,
                can_send_games=not denied_permissions.send_games,
                can_send_inline=not denied_permissions.send_inline,
                can_embed_links=not denied_permissions.embed_links,
                can_send_polls=not denied_permissions.send_polls,
                can_change_info=not denied_permissions.change_info,
                can_invite_users=not denied_permissions.invite_users,
                can_pin_messages=not denied_permissions.pin_messages,
                can_manage_topics=not denied_permissions.manage_topics,
                can_send_photos=not denied_permissions.send_photos,
                can_send_videos=not denied_permissions.send_videos,
                can_send_roundvideos=not denied_permissions.send_roundvideos,
                can_send_audios=not denied_permissions.send_audios,
                can_send_voices=not denied_permissions.send_voices,
                can_send_docs=not denied_permissions.send_docs,
                can_send_plain=not denied_permissions.send_plain,
            )

    @property
    def can_send_media_messages(self) -> bool:
        warn(
            'This property is deprecated. Use can_send_media instead',
            DeprecationWarning,
            stacklevel=2
        )
        # DEPRECATED
        return self.can_send_media

    @property
    def can_send_other_messages(self) -> bool:
        warn(
            'This property is deprecated. '
            'Use can_send_stickers, can_send_gifs, can_send_games, can_send_inline instead',
            DeprecationWarning,
            stacklevel=2
        )
        # DEPRECATED
        return any([
            self.can_send_stickers,
            self.can_send_gifs,
            self.can_send_games,
            self.can_send_inline
        ])

    @property
    def can_add_web_page_previews(self) -> bool:
        warn(
            'This property is deprecated. '
            'Use can_embed_links',
            DeprecationWarning,
            stacklevel=2
        )
        return self.can_embed_links
