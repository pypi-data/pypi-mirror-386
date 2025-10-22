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
from pylogram.typevars import HandlerCallable
from pylogram.typevars import HandlerDecorator


class OnDisconnect:
    def on_disconnect(self=None) -> HandlerDecorator:
        """Decorator for handling disconnections.

        This does the same thing as :meth:`~pylogram.Client.add_handler` using the
        :obj:`~pylogram.handlers.DisconnectHandler`.
        """

        def decorator(func: HandlerCallable) -> HandlerCallable:
            if isinstance(self, pylogram.Client):
                self.add_handler(pylogram.handlers.DisconnectHandler(func))
            else:
                if not hasattr(func, "handlers"):
                    func.handlers = []

                func.handlers.append((pylogram.handlers.DisconnectHandler(func), 0))

            return func

        return decorator
