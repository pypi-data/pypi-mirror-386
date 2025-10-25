"""Module for mapping Pydantic validation error codes to messages in Russian.

This module provides a dictionary that maps common Pydantic error types to descriptive
error messages in Russian, used for user-friendly validation feedback.
"""

from typing import Final

PYDANTIC_ERROR_TYPES: dict[str, str] = {
    "missing": "Не заполнено обязательное поле",
    "uuid_parsing": "Невалидное значение для UUID",
    "uuid_type": "Невалидное значение для UUID",
    "uuid_version": "Невалидное значение для UUID",
    "bool_parsing": "Невалидное значение для логического типа(bool)",
    "bool_type": "Невалидное значение для логического типа(bool)",
    "date_type": "Невалидное значение даты(date)",
    "datetime_from_date_parsing": "Невалидное значение даты и времени(datetime)",
    "datetime_type": "Невалидное значение даты и времени(datetime)",
    "dict_type": "Невалидное значение словаря",
    "list_type": "Невалидное значение списка",
    "string_type": "Невалидное строковое значение(str)",
    "enum": "Невалидное значение Enum",
    "float_parsing": "Невалидное значение числа с плавающей точкой(float)",
    "float_type": "Невалидное значение числа с плавающей точкой(float)",
    "int_from_float": "Невалидное значение для целочисленного числа(int)",
    "int_parsing": "Невалидное значение для целочисленного числа(int)",
    "int_parsing_size": "Невалидное значение для целочисленного числа(int)",
    "int_type": "Невалидное значение для целочисленного числа(int)",
    "non_negative_int": "Невалидное значение для целочисленного числа(int), "
    "должно быть больше или равно 0",
    "incorrect_latitude": "Некорректное значение широты, должно быть больше, "
    "чем -90.0 и меньше, чем 90.0",
    "incorrect_longitude": "Некорректное значение долготы, должно быть больше, "
    "чем -180.0 и меньше, чем 180.0",
    "string_too_short": "Cтрока слишком короткая",
    "ip_address": "Невалидное значение адреса IPv4/IPv6",
    "incorrect_email": "Невалидное значение email-адреса",
    "list_expected": "Некорректный тип данных. Ожидается список.",
}
UNKNOWN_ERROR_TYPE: Final[str] = "Неизвестная ошибка"
