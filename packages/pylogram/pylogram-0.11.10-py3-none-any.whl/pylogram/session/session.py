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
import bisect
import logging
import os
from hashlib import sha1
from io import BytesIO
from typing import Type

import pylogram
from pylogram import raw
from pylogram.connection import Connection
from pylogram.crypto import mtproto
from pylogram.errors import AuthKeyDuplicated
from pylogram.errors import BadMsgNotification
from pylogram.errors import FloodWait
from pylogram.errors import InternalServerError
from pylogram.errors import RPCError
from pylogram.errors import SecurityCheckMismatch
from pylogram.errors import ServiceUnavailable
from pylogram.raw.all import layer
from pylogram.raw.core import FutureSalts
from pylogram.raw.core import Int
from pylogram.raw.core import MsgContainer
from pylogram.raw.core import TLObject
from .internals import MsgFactory
from .internals import MsgId
from ..connection.transport import TCP
from ..connection.transport import TCPFull

log = logging.getLogger(__name__)


class Result:
    def __init__(self):
        self.value = None
        self.event = asyncio.Event()


class Session:
    START_TIMEOUT = 2
    WAIT_TIMEOUT = 15
    SLEEP_THRESHOLD = 10
    MAX_RETRIES = 10
    ACKS_THRESHOLD = 10
    PING_INTERVAL = 5
    STORED_MSG_IDS_MAX_SIZE = 1000 * 2

    TRANSPORT_ERRORS = {
        404: "auth key not found",
        429: "transport flood",
        444: "invalid DC"
    }

    def __init__(
            self,
            client: "pylogram.Client",
            dc_id: int,
            auth_key: bytes,
            test_mode: bool,
            is_media: bool = False,
            is_cdn: bool = False,
            *,
            connection_protocol_class: Type[TCP] = TCPFull
    ):
        self.client = client
        self.dc_id = dc_id
        self.auth_key = auth_key
        self.test_mode = test_mode
        self.is_media = is_media
        self.is_cdn = is_cdn
        self.connection = None
        self.auth_key_id = sha1(auth_key).digest()[-8:]
        self.session_id = os.urandom(8)
        self.msg_factory = MsgFactory()
        self.salt = 0
        self.pending_acks = set()
        self.results = {}
        self.stored_msg_ids = []
        self.ping_task = None
        self.ping_task_event = asyncio.Event()
        self.recv_task = None
        self.is_started = asyncio.Event()
        self.background_tasks = set()
        self.updates_handling_tasks = set()
        self.connection_protocol_class = connection_protocol_class

    async def start(self):
        while True:
            self.connection = Connection(
                self.dc_id,
                self.test_mode,
                self.client.ipv6,
                self.client.proxy,
                self.is_media,
                protocol_class=self.connection_protocol_class
            )

            api_id = self.client.api_id

            if not bool(api_id):
                api_id = await self.client.storage.api_id()

            if not bool(api_id):
                raise RuntimeError("Cannot execute InitConnection without api_id")

            try:
                await self.connection.connect()
                self.recv_task = asyncio.create_task(self.recv_worker())
                await self.send(raw.functions.Ping(ping_id=0), timeout=self.START_TIMEOUT)

                if not self.is_cdn:
                    await self.send(
                        raw.functions.InvokeWithLayer(
                            layer=layer,
                            query=raw.functions.InitConnection(
                                api_id=api_id,
                                device_model=self.client.device_model,
                                system_version=self.client.system_version,
                                app_version=self.client.app_version,
                                system_lang_code=self.client.system_lang_code,
                                lang_pack=self.client.lang_pack or "",
                                lang_code=self.client.lang_code,
                                query=raw.functions.help.GetConfig(),
                            )
                        ),
                        timeout=self.START_TIMEOUT
                    )

                self.ping_task = asyncio.create_task(self.ping_worker())

                log.info("Session initialized: Layer %s", layer)
                log.info("Device: %s - %s", self.client.device_model, self.client.app_version)
                log.info("System: %s (%s)", self.client.system_version, self.client.system_lang_code.upper())
            except AuthKeyDuplicated as e:
                await self.stop()
                raise e
            except (OSError, RPCError):
                await self.stop()
            except Exception as e:
                await self.stop()
                raise e
            else:
                break

        self.is_started.set()

        log.info("Session started")

    async def stop(self):
        self.is_started.clear()
        self.stored_msg_ids.clear()
        self.ping_task_event.set()

        if self.ping_task is not None:
            await self.ping_task

        self.ping_task_event.clear()

        await self.connection.close()

        if self.recv_task:
            await self.recv_task

        if not self.is_media and callable(self.client.disconnect_handler):
            try:
                await self.client.disconnect_handler(self.client)
            except Exception as e:
                log.exception(e)

        log.info("Session stopped")

    async def restart(self):
        await self.stop()
        await self.start()

    def _create_task(self, coro) -> asyncio.Task:
        # Use Best Practices from official python docs
        # https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
        t = asyncio.create_task(coro)
        self.background_tasks.add(t)
        t.add_done_callback(self.background_tasks.discard)
        return t

    async def handle_packet(self, packet):
        data = await asyncio.to_thread(
            mtproto.unpack,
            BytesIO(packet),
            self.session_id,
            self.auth_key,
            self.auth_key_id
        )

        messages = (
            data.body.messages
            if isinstance(data.body, MsgContainer)
            else [data]
        )

        log.debug("Received: %s", data)

        for msg in messages:
            if msg.seq_no % 2 != 0:
                if msg.msg_id in self.pending_acks:
                    continue
                else:
                    self.pending_acks.add(msg.msg_id)

            try:
                if len(self.stored_msg_ids) > Session.STORED_MSG_IDS_MAX_SIZE:
                    del self.stored_msg_ids[:Session.STORED_MSG_IDS_MAX_SIZE // 2]

                if self.stored_msg_ids:
                    if msg.msg_id < self.stored_msg_ids[0]:
                        raise SecurityCheckMismatch("The msg_id is lower than all the stored values")

                    if msg.msg_id in self.stored_msg_ids:
                        raise SecurityCheckMismatch("The msg_id is equal to any of the stored values")

                    time_diff = (msg.msg_id - MsgId()) / 2 ** 32

                    if time_diff > 30:
                        raise SecurityCheckMismatch("The msg_id belongs to over 30 seconds in the future. "
                                                    "Most likely the client time has to be synchronized.")

                    if time_diff < -300:
                        raise SecurityCheckMismatch("The msg_id belongs to over 300 seconds in the past. "
                                                    "Most likely the client time has to be synchronized.")
            except SecurityCheckMismatch as e:
                log.info("Discarding packet: %s", e)
                await self.connection.close()
                return
            else:
                bisect.insort(self.stored_msg_ids, msg.msg_id)

            if isinstance(msg.body, (raw.types.MsgDetailedInfo, raw.types.MsgNewDetailedInfo)):
                self.pending_acks.add(msg.body.answer_msg_id)
                continue

            if isinstance(msg.body, raw.types.NewSessionCreated):
                continue

            msg_id = None

            if isinstance(msg.body, (raw.types.BadMsgNotification, raw.types.BadServerSalt)):
                msg_id = msg.body.bad_msg_id
            elif isinstance(msg.body, (FutureSalts, raw.types.RpcResult)):
                msg_id = msg.body.req_msg_id
            elif isinstance(msg.body, raw.types.Pong):
                msg_id = msg.body.msg_id
            else:
                if self.client is not None:
                    self._create_task(self.client.handle_updates(msg.body))

            if msg_id in self.results:
                self.results[msg_id].value = getattr(msg.body, "result", msg.body)
                self.results[msg_id].event.set()

        if len(self.pending_acks) >= self.ACKS_THRESHOLD:
            log.debug("Sending %s acks", len(self.pending_acks))

            try:
                await self.send(raw.types.MsgsAck(msg_ids=list(self.pending_acks)), False)
            except OSError:
                pass
            else:
                self.pending_acks.clear()

    async def ping_worker(self):
        log.info("PingTask started")

        while True:
            try:
                await asyncio.wait_for(self.ping_task_event.wait(), self.PING_INTERVAL)
            except (asyncio.TimeoutError, TimeoutError):
                pass
            else:
                break

            try:
                await self.send(
                    raw.functions.PingDelayDisconnect(
                        ping_id=0, disconnect_delay=self.WAIT_TIMEOUT + 10
                    ), False
                )
            except (OSError, RPCError):
                pass

        log.info("PingTask stopped")

    async def recv_worker(self):
        log.info("NetworkTask started")

        while True:
            packet = await self.connection.recv()

            if packet is None or len(packet) == 4:
                if packet:
                    error_code = -Int.read(BytesIO(packet))

                    log.warning(
                        "Server sent transport error: %s (%s)",
                        error_code, Session.TRANSPORT_ERRORS.get(error_code, "unknown error")
                    )

                if self.is_started.is_set():
                    self._create_task(self.restart())

                break

            self._create_task(self.handle_packet(packet))

        log.info("NetworkTask stopped")

    async def send(self, data: TLObject, wait_response: bool = True, timeout: float = WAIT_TIMEOUT):
        message = self.msg_factory(data)
        msg_id = message.msg_id

        if wait_response:
            self.results[msg_id] = Result()

        log.debug("Sent: %s", message)
        # payload = mtproto.pack(
        #     message,
        #     self.salt,
        #     self.session_id,
        #     self.auth_key,
        #     self.auth_key_id
        # )
        payload = await asyncio.to_thread(
            mtproto.pack,
            message,
            self.salt,
            self.session_id,
            self.auth_key,
            self.auth_key_id
        )

        try:
            await self.connection.send(payload)
        except OSError as e:
            self.results.pop(msg_id, None)
            raise e

        if wait_response:
            try:
                await asyncio.wait_for(self.results[msg_id].event.wait(), timeout)
            except (asyncio.TimeoutError, TimeoutError):
                pass

            result = self.results.pop(msg_id).value

            if result is None:
                raise TimeoutError("Request timed out")

            if isinstance(result, raw.types.RpcError):
                if isinstance(data, (raw.functions.InvokeWithoutUpdates, raw.functions.InvokeWithTakeout)):
                    data = data.query

                RPCError.raise_it(result, type(data))

            if isinstance(result, raw.types.BadMsgNotification):
                log.warning("%s: %s", BadMsgNotification.__name__, BadMsgNotification(result.error_code))

            if isinstance(result, raw.types.BadServerSalt):
                self.salt = result.new_server_salt
                return await self.send(data, wait_response, timeout)

            return result

    async def invoke(
            self,
            query: TLObject,
            retries: int = MAX_RETRIES,
            timeout: float = WAIT_TIMEOUT,
            sleep_threshold: float = SLEEP_THRESHOLD
    ):
        try:
            await asyncio.wait_for(self.is_started.wait(), self.WAIT_TIMEOUT)
        except (asyncio.TimeoutError, TimeoutError):
            pass

        if isinstance(query, (raw.functions.InvokeWithoutUpdates, raw.functions.InvokeWithTakeout)):
            inner_query = query.query
        else:
            inner_query = query

        query_name = ".".join(inner_query.QUALNAME.split(".")[1:])

        while True:
            try:
                return await self.send(query, timeout=timeout)
            except FloodWait as e:
                amount = e.value

                if amount > sleep_threshold >= 0:
                    raise

                log.warning('[%s] Waiting for %s seconds before continuing (required by "%s")',
                            self.client.session_name, amount, query_name)

                await asyncio.sleep(amount)
            except (OSError, InternalServerError, ServiceUnavailable) as e:
                if retries == 0:
                    raise e from None

                (log.warning if retries < 2 else log.info)(
                    '[%s] Retrying "%s" due to: %s',
                    Session.MAX_RETRIES - retries + 1,
                    query_name, str(e) or repr(e)
                )

                await asyncio.sleep(0.5)

                return await self.invoke(query, retries - 1, timeout)
