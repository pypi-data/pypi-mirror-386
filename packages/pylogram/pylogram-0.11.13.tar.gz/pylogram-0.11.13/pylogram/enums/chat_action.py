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


class ChatAction(AutoName):
    """Chat action enumeration used in :obj:`~pylogram.types.ChatEvent`."""

    TYPING = raw.types.SendMessageTypingAction
    "Typing text message"

    UPLOAD_PHOTO = raw.types.SendMessageUploadPhotoAction
    "Uploading photo"

    RECORD_VIDEO = raw.types.SendMessageRecordVideoAction
    "Recording video"

    UPLOAD_VIDEO = raw.types.SendMessageUploadVideoAction
    "Uploading video"

    RECORD_AUDIO = raw.types.SendMessageRecordAudioAction
    "Recording audio"

    UPLOAD_AUDIO = raw.types.SendMessageUploadAudioAction
    "Uploading audio"

    UPLOAD_DOCUMENT = raw.types.SendMessageUploadDocumentAction
    "Uploading document"

    FIND_LOCATION = raw.types.SendMessageGeoLocationAction
    "Finding location"

    RECORD_VIDEO_NOTE = raw.types.SendMessageRecordRoundAction
    "Recording video note"

    UPLOAD_VIDEO_NOTE = raw.types.SendMessageUploadRoundAction
    "Uploading video note"

    PLAYING = raw.types.SendMessageGamePlayAction
    "Playing game"

    CHOOSE_CONTACT = raw.types.SendMessageChooseContactAction
    "Choosing contact"

    SPEAKING = raw.types.SpeakingInGroupCallAction
    "Speaking in group call"

    IMPORT_HISTORY = raw.types.SendMessageHistoryImportAction
    "Importing history"

    CHOOSE_STICKER = raw.types.SendMessageChooseStickerAction
    "Choosing sticker"

    CANCEL = raw.types.SendMessageCancelAction
    "Cancel ongoing chat action"
