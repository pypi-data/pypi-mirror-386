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
import asyncio

import pylogram


class Stop:
    async def stop(
            self: "pylogram.Client",
            block: bool = True
    ):
        """Stop the Client.

        This method disconnects the client from Telegram and stops the underlying tasks.

        Parameters:
            block (``bool``, *optional*):
                Blocks the code execution until the client has been stopped. It is useful with ``block=False`` in case
                you want to stop the own client *within* a handler in order not to cause a deadlock.
                Defaults to True.

        Returns:
            :obj:`~pylogram.Client`: The stopped client itself.

        Raises:
            ConnectionError: In case you try to stop an already stopped client.

        Example:
            .. code-block:: python

                from pylogram import Client

                app = Client("my_account")


                async def main():
                    await app.start()
                    ...  # Invoke API methods
                    await app.stop()


                app.run(main())
        """

        async def do_it():
            await self.terminate()
            await self.disconnect()

        if block:
            await do_it()
        else:
            _ = asyncio.create_task(do_it())

        return self
