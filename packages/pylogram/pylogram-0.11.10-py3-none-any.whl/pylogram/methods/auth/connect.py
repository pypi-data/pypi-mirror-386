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

import pylogram
from pylogram.session import Session


class Connect:
    async def connect(
        self: "pylogram.Client",
    ) -> bool:
        """
        Connect the client to Telegram servers.

        Returns:
            ``bool``: On success, in case the passed-in session is authorized, True is returned. Otherwise, in case
            the session needs to be authorized, False is returned.

        Raises:
            ConnectionError: In case you try to connect an already connected client.
        """
        if self.is_connected:
            raise ConnectionError("Client is already connected")

        await self.load_session()

        self.session = Session(
            self,
            await self.storage.dc_id(),
            await self.storage.auth_key(),
            await self.storage.test_mode(),
            is_media=False,
            is_cdn=False,
            connection_protocol_class=self.connection_protocol_class,
        )

        await self.session.start()

        self.is_connected = True

        return bool(await self.storage.user_id())
