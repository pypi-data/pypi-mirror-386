#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УРАБИ.РФ - Криптографические и телекоммуникационные решения

Пакет содержит отечественные реализации криптографических алгоритмов,
SIP телефонии и блокчейн решений в соответствии с российскими стандартами.
"""

__version__ = "1.0.0"
__author__ = "УРАБИ.РФ"
__email__ = "info@ураби.рф"

# Импорт основных модулей
from . import crypto
from . import sip
from . import blockchain

# Основные классы для импорта
__all__ = [
    "crypto",
    "sip",
    "blockchain",
    "__version__",
    "__author__",
    "__email__",
]

# Информация о пакете
PACKAGE_INFO = {
    "name": "УРАБИ Криптографические Решения",
    "description": "Отечественные криптографические и телекоммуникационные решения",
    "version": __version__,
    "author": __author__,
    "specializations": [
        "ГОСТ Криптография",
        "SIP Телефония",
        "Блокчейн Решения",
        "Цифровые Подписи",
        "Хеш-функции",
        "Шифрование"
    ],
    "standards": [
        "ГОСТ Р 34.10-2012",
        "ГОСТ Р 34.11-2012", 
        "ГОСТ 28147-89",
        "ГОСТ Р 50.1.111-2016",
        "Российские стандарты безопасности"
    ],
    "compliance": [
        "ФСТЭК России",
        "ФСБ России",
        "Роскомнадзор",
        "ГОСТ стандарты"
    ]
}

def get_package_info():
    """Получить информацию о пакете УРАБИ"""
    return PACKAGE_INFO.copy()

def get_specializations():
    """Получить список специализаций"""
    return PACKAGE_INFO["specializations"].copy()

def get_standards():
    """Получить список поддерживаемых стандартов"""
    return PACKAGE_INFO["standards"].copy()

def get_compliance():
    """Получить список соответствий"""
    return PACKAGE_INFO["compliance"].copy()
