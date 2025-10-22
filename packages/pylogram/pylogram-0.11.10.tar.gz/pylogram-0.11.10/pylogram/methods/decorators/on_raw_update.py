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
from pylogram.typevars import RawHandlerCallable
from pylogram.typevars import RawHandlerDecorator


class OnRawUpdate:
    def on_raw_update(
            self=None,
            group: int = 0
    ) -> RawHandlerDecorator:
        """Decorator for handling raw updates.

        This does the same thing as :meth:`~pylogram.Client.add_handler` using the
        :obj:`~pylogram.handlers.RawUpdateHandler`.

        Parameters:
            group (``int``, *optional*):
                The group identifier, defaults to 0.
        """

        def decorator(func: RawHandlerCallable) -> RawHandlerCallable:
            if isinstance(self, pylogram.Client):
                self.add_handler(pylogram.handlers.RawUpdateHandler(func), group)
            else:
                if not hasattr(func, "handlers"):
                    func.handlers = []

                func.handlers.append(
                    (
                        pylogram.handlers.RawUpdateHandler(func),
                        group
                    )
                )

            return func

        return decorator
