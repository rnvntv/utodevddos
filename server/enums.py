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
    TERMINATE = -1
    #: Остановить атаку и перейти в режим ожидания.
    STOP = 0
    #: Пожалуйста, выполните чтение для получения адреса цели.
    READ_TARGET = 1


class ClientCommands(IntEnum):
    """
    Различные команды, отправляемые клиентом UtodevBotnet.
    """
    #: Что-то пошло не так.
    ERROR = -2
    #: Бот завершен.
    KILLED = -1
    #: Остановлена предыдущая атака, в режиме ожидания.
    STANDBY = 0
    #: Отправьте мне адрес цели.
    SEND_TARGET = 1
    #: Пожалуйста, выполните чтение для получения статуса.
    READ_STATUS = 2


class StatusCodes(IntEnum):
    """
    Различные коды ошибок HTTP.
    """
    CONNECTION_FAILURE = 69
    NO_LUCK = 200
    ANTI_DDOS = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    PWNED = 500


class ErrorMessages(IntEnum):
    """
    Сообщения об ошибках во время связи сервер-клиент.
    """
    CONNECTION_ABORTED = 1
    CONNECTION_REFUSED = 2
    CONNECTION_RESET = 3
