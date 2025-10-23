__all__ = ["Websocket"]

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import orjson
import websockets
from loguru import logger as _logger
from websockets.asyncio.client import ClientConnection

from unicex.exceptions import QueueOverflowError
from unicex.types import LoggerLike


class Websocket:
    """Базовый класс асинхронного вебсокета."""

    MAX_QUEUE_SIZE: int = 100
    """Максимальная длина очереди."""

    class _DecoderProtocol(Protocol):
        """Протокол декодирования сообщений."""

        def decode(self, message: Any) -> dict: ...

    class _JsonDecoder:
        """Протокол декодирования сообщений в формате JSON."""

        def decode(self, message: Any) -> dict:
            return orjson.loads(message)

    def __init__(
        self,
        callback: Callable[[Any], Awaitable[None]],
        url: str,
        subscription_messages: list[dict] | list[str] | None = None,
        ping_interval: int | float = 10,
        ping_message: str | Callable | None = None,
        pong_message: str | Callable | None = None,
        no_message_reconnect_timeout: int | float | None = 60,
        reconnect_timeout: int | float | None = 5,
        worker_count: int = 1,
        logger: LoggerLike | None = None,
        decoder: type[_DecoderProtocol] = _JsonDecoder,
        **kwargs: Any,  # Не дадим сломаться, если юзер передал ненужные аргументы
    ) -> None:
        """Инициализация вебсокета.

        Параметры:
            callback (`Callable[[Any], Awaitable[None]]`): Обработчик входящих сообщений.
            url (`str`): URL вебсокета.
            subscription_messages (`list[dict] | list[str] | None`): Сообщения для подписки после подключения.
            ping_interval (`int | float`): Интервал отправки ping, сек.
            ping_message (`str | Callable | None`): Сообщение для ping, или функция генерации ping (если не указано — используется ping‑frame).
            pong_message (`str | Callable | None`): Сообщение для pong, или функция генерации pong (если не указано — используется pong‑frame).
            no_message_reconnect_timeout (`int | float | None`): Таймаут ожидания без сообщений до рестарта, сек.
            reconnect_timeout (`int | float | None`): Пауза перед переподключением, сек.
            worker_count (`int`): Количество рабочих задач для обработки сообщений.
            logger (`LoggerLike | None`): Логгер для записи логов.
            decoder (`IDecoder | None`): Декодер для обработки входящих сообщений.
        """
        self._callback = callback
        self._url = url
        self._subscription_messages = subscription_messages or []
        self._ping_interval = ping_interval
        self._ping_message = ping_message
        self._pong_message = pong_message
        self._no_message_reconnect_timeout = no_message_reconnect_timeout
        self._reconnect_timeout = reconnect_timeout or 0
        self._last_message_time = time.monotonic()
        self._worker_count = worker_count
        self._logger = logger or _logger
        self._decoder = decoder()
        self._tasks: list[asyncio.Task] = []
        self._queue = asyncio.Queue()
        self._running = False

    async def start(self) -> None:
        """Запускает вебсокет и рабочие задачи."""
        # Проверяем что вебсокет еще не запущен
        if self._running:
            raise RuntimeError("Websocket is already running")
        self._running = True

        # Запускаем вебсокет
        try:
            await self._connect()
        except Exception as e:
            self._logger.error(f"Failed to connect to websocket: {e}")
            self._running = False
            raise

    async def stop(self) -> None:
        """Останавливает вебсокет и рабочие задачи."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

        # Очистка очереди
        self._queue = asyncio.Queue()

    async def restart(self) -> None:
        """Перезапускает вебсокет."""
        await self.stop()
        await asyncio.sleep(self._reconnect_timeout)
        await self.start()

    async def _connect(self) -> None:
        """Подключается к вебсокету и настраивает соединение."""
        self._logger.debug(f"Establishing connection with {self._url}")
        while self._running:
            async with websockets.connect(uri=self._url, **self._generate_ws_kwargs()) as conn:
                try:
                    self._logger.info(f"Websocket connection was established to {self._url}")
                    await self._after_connect(conn)

                    # Цикл получения сообщений
                    while self._running:
                        message = await conn.recv()
                        await self._handle_message(message)

                except websockets.exceptions.ConnectionClosed as e:
                    self._logger.error(f"Websocket connection was closed unexpectedly: {e}")
                except Exception as e:
                    self._logger.error(f"Unexpected error in websosocket connection: {e}")
                finally:
                    if self._running:
                        await asyncio.sleep(self._reconnect_timeout)
                        await self._after_disconnect()

    async def _handle_message(self, message: str | bytes) -> None:
        """Обрабатывает входящее сообщение вебсокета."""
        try:
            # Обновленяем время последнего сообщения
            self._last_message_time = time.monotonic()

            # Ложим сообщение в очередь, предварительно его сериализуя
            decoded_message = self._decoder.decode(message)
            await self._queue.put(decoded_message)

            # Проверяем размер очереди сообщений и выбрасываем ошибку, если он превышает максимальный размер
            self._check_queue_size()
        except QueueOverflowError:
            self._logger.error("Message queue is overflow")
        except orjson.JSONDecodeError as e:
            if message in ["ping", "pong"]:
                self._logger.debug(f"Received ping message: {message}")
            else:
                self._logger.error(f"Failed to decode JSON message: {message}, error: {e}")
        except Exception as e:
            self._logger.error(f"Unexpected error: {e}")

    def _check_queue_size(self) -> None:
        """Проверяет размер очереди и выбрасывает ошибку при переполнении."""
        qsize = self._queue.qsize()
        if qsize >= self.MAX_QUEUE_SIZE:
            raise QueueOverflowError(f"Message queue is overflow: {qsize}")

    async def _after_connect(self, conn: ClientConnection) -> None:
        """Вызывается после установки соединения."""
        # Подписываемся на топики
        await self._send_subscribe_messages(conn)

        # Обновленяем время последнего сообщения перед каждым подключением
        self._last_message_time = time.monotonic()

        # Запускам задачу для кастомного пинг сообщения
        if self._ping_message:
            self._tasks.append(asyncio.create_task(self._custom_ping_task(conn)))

        # Запускаем healthcheck
        if self._no_message_reconnect_timeout:
            self._tasks.append(asyncio.create_task(self._healthcheck_task()))

        # Запускаем воркеров
        for _ in range(self._worker_count):
            task = asyncio.create_task(self._worker())
            self._tasks.append(task)

    async def _after_disconnect(self) -> None:
        """Вызывается после отключения от вебсокета."""
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

        # Очистить очередь
        self._queue = asyncio.Queue()

    async def _send_subscribe_messages(self, conn: ClientConnection) -> None:
        """Отправляет сообщения с подпиской на топики, если нужно."""
        for message in self._subscription_messages:
            await conn.send(message)
            self._logger.debug(f"Sent subscribe message: {message}")

    async def _worker(self) -> None:
        """Обрабатывает сообщения из очереди."""
        while self._running:
            try:
                data = await self._queue.get()  # Получаем сообщение
                await self._callback(data)  # Передаем в callback
                self._queue.task_done()
            except asyncio.exceptions.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error({type(e)}) while processing message: {e}")

    def _generate_ws_kwargs(self) -> dict:
        """Генерирует аргументы для запуска вебсокета."""
        ws_kwargs = {}
        if self._ping_interval:
            ws_kwargs["ping_interval"] = self._ping_interval
        return ws_kwargs

    async def _custom_ping_task(self, conn: ClientConnection) -> None:
        """Периодически отправляет пользовательский ping."""
        while self._running and self._ping_message:
            try:
                if isinstance(self._ping_message, Callable):
                    ping_message = self._ping_message()
                else:
                    ping_message = self._ping_message
                await conn.send(ping_message)
                self._logger.debug(f"Sent ping message: {ping_message}")
            except Exception as e:
                self._logger.error(f"Error sending ping: {e}")
                return
            await asyncio.sleep(self._ping_interval)

    async def _healthcheck_task(self) -> None:
        """Следит за таймаутом получения сообщений."""
        if not self._no_message_reconnect_timeout:
            return

        while self._running:
            if time.monotonic() - self._last_message_time > self._no_message_reconnect_timeout:
                self._logger.error("Websocket is not responding, restarting...")
                await self.restart()
                return
            await asyncio.sleep(1)

    def __repr__(self) -> str:
        """Репрезентация вебсокета."""
        return f"<Websocket(url={self._url[:15]}...)>"
