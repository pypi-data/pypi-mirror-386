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

from io import BytesIO

from pylogram.raw.core.primitives import Int, Long, Int128, Int256, Bool, Bytes, String, Double, Vector
from pylogram.raw.core import TLObject
from pylogram import raw
from typing import List, Optional, Any

# # # # # # # # # # # # # # # # # # # # # # # #
#               !!! WARNING !!!               #
#          This is a generated file!          #
# All changes made in this file will be lost! #
# # # # # # # # # # # # # # # # # # # # # # # #


class InputChatUploadedPhoto(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pylogram.raw.base.InputChatPhoto`.

    Details:
        - Layer: ``181``
        - ID: ``BDCDAEC0``

    Parameters:
        file (:obj:`InputFile <pylogram.raw.base.InputFile>`, *optional*):
            N/A

        video (:obj:`InputFile <pylogram.raw.base.InputFile>`, *optional*):
            N/A

        video_start_ts (``float`` ``64-bit``, *optional*):
            N/A

        video_emoji_markup (:obj:`VideoSize <pylogram.raw.base.VideoSize>`, *optional*):
            N/A

    """

    __slots__: List[str] = ["file", "video", "video_start_ts", "video_emoji_markup"]

    ID = 0xbdcdaec0
    QUALNAME = "types.InputChatUploadedPhoto"

    def __init__(self, *, file: "raw.base.InputFile" = None, video: "raw.base.InputFile" = None, video_start_ts: Optional[float] = None, video_emoji_markup: "raw.base.VideoSize" = None) -> None:
        self.file = file  # flags.0?InputFile
        self.video = video  # flags.1?InputFile
        self.video_start_ts = video_start_ts  # flags.2?double
        self.video_emoji_markup = video_emoji_markup  # flags.3?VideoSize

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "InputChatUploadedPhoto":
        
        flags = Int.read(b)
        
        file = TLObject.read(b) if flags & (1 << 0) else None
        
        video = TLObject.read(b) if flags & (1 << 1) else None
        
        video_start_ts = Double.read(b) if flags & (1 << 2) else None
        video_emoji_markup = TLObject.read(b) if flags & (1 << 3) else None
        
        return InputChatUploadedPhoto(file=file, video=video, video_start_ts=video_start_ts, video_emoji_markup=video_emoji_markup)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        flags = 0
        flags |= (1 << 0) if self.file is not None else 0
        flags |= (1 << 1) if self.video is not None else 0
        flags |= (1 << 2) if self.video_start_ts is not None else 0
        flags |= (1 << 3) if self.video_emoji_markup is not None else 0
        b.write(Int(flags))
        
        if self.file is not None:
            b.write(self.file.write())
        
        if self.video is not None:
            b.write(self.video.write())
        
        if self.video_start_ts is not None:
            b.write(Double(self.video_start_ts))
        
        if self.video_emoji_markup is not None:
            b.write(self.video_emoji_markup.write())
        
        return b.getvalue()
