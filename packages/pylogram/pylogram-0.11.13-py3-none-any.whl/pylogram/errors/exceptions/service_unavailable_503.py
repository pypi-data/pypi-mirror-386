# Pylogram - Telegram MTProto API Client Library for Python
# Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
# Copyright (C) 2023-2024 Pylakey <https://github.com/pylakey>
#
# This file is part of Pylogram.
#
# Pylogram is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pylogram is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Pylogram.  If not, see <http://www.gnu.org/licenses/>.

from ..rpc_error import RPCError


class ServiceUnavailable(RPCError):
    """Service Unavailable"""
    CODE = 503
    """``int``: RPC Error Code"""
    NAME = __doc__


class ApiCallError(ServiceUnavailable):
    """Telegram is having internal problems. Please try again later."""
    ID = "ApiCallError"
    """``str``: RPC Error ID"""
    MESSAGE = __doc__


class Timedout(ServiceUnavailable):
    """Telegram is having internal problems. Please try again later."""
    ID = "Timedout"
    """``str``: RPC Error ID"""
    MESSAGE = __doc__


class Timeout(ServiceUnavailable):
    """Telegram is having internal problems. Please try again later."""
    ID = "Timeout"
    """``str``: RPC Error ID"""
    MESSAGE = __doc__


