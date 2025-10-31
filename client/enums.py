#!/usr/bin/env python3

"""
UtodevBotnet v3

Этот модуль содержит перечисления, используемые в UtodevBotnet.
"""

# pylint: disable=duplicate-code
from enum import IntEnum


class ServerCommands(IntEnum):
    """
    Различные команды, отправляемые сервером UtodevBotnet.
    """
    #: Убить бота.
    TERMINATE: int = -1
    #: Остановить атаку и перейти в режим ожидания.
    STOP: int = 0
    #: Пожалуйста, выполните чтение для получения адреса цели.
    READ_TARGET: int = 1


class ClientCommands(IntEnum):
    """
    Различные команды, отправляемые клиентом UtodevBotnet.
    """
    #: Что-то пошло не так.
    ERROR: int = -2
    #: Бот завершен.
    KILLED: int = -1
    #: Остановлена предыдущая атака, в режиме ожидания.
    STANDBY: int = 0
    #: Отправьте мне адрес цели.
    SEND_TARGET: int = 1
    #: Пожалуйста, выполните чтение для получения статуса.
    READ_STATUS: int = 2


class StatusCodes(IntEnum):
    """
    Различные коды ошибок HTTP.
    """
    CONNECTION_FAILURE: int = 69
    NO_LUCK: int = 200
    ANTI_DDOS: int = 400
    FORBIDDEN: int = 403
    NOT_FOUND: int = 404
    PWNED: int = 500
