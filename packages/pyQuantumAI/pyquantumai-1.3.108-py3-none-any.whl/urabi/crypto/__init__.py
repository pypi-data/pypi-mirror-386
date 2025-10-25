#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УРАБИ Криптография - Отечественные криптографические алгоритмы

Модуль содержит реализации российских криптографических стандартов:
- ГОСТ Р 34.10-2012 (цифровые подписи)
- ГОСТ Р 34.11-2012 (хеш-функции)
- ГОСТ 28147-89 (шифрование)
- ГОСТ Р 50.1.111-2016 (криптографическая защита)
"""

__version__ = "1.0.0"
__author__ = "УРАБИ.РФ"

# Импорт основных классов
from .gost_crypto import GOSTCrypto
from .gost_hash import GOSTHash
from .gost_signature import GOSTSignature
from .gost_encryption import GOSTEncryption
from .quantum_crypto import QuantumCrypto

# Основные классы для импорта
__all__ = [
    "GOSTCrypto",
    "GOSTHash",
    "GOSTSignature", 
    "GOSTEncryption",
    "QuantumCrypto",
    "__version__",
    "__author__",
]

# Информация о модуле
MODULE_INFO = {
    "name": "УРАБИ Криптография",
    "description": "Отечественные криптографические алгоритмы ГОСТ",
    "version": __version__,
    "author": __author__,
    "algorithms": {
        "ГОСТ Р 34.10-2012": "Цифровые подписи",
        "ГОСТ Р 34.11-2012": "Хеш-функции",
        "ГОСТ 28147-89": "Блочное шифрование",
        "ГОСТ Р 50.1.111-2016": "Криптографическая защита"
    },
    "features": [
        "Полное соответствие ГОСТ стандартам",
        "Интеграция с квантовой криптографией",
        "Оптимизация под российские процессоры",
        "Поддержка отечественных ОС",
        "Сертификация ФСТЭК и ФСБ",
        "Высокая производительность"
    ],
    "quantum_features": [
        "Квантовая криптография",
        "Квантовые случайные числа",
        "Квантовая защита от атак",
        "Постквантовая криптография"
    ]
}

def get_module_info():
    """Получить информацию о модуле криптографии"""
    return MODULE_INFO.copy()

def get_algorithms():
    """Получить список поддерживаемых алгоритмов"""
    return MODULE_INFO["algorithms"].copy()

def get_features():
    """Получить список возможностей"""
    return MODULE_INFO["features"].copy()

def get_quantum_features():
    """Получить список квантовых возможностей"""
    return MODULE_INFO["quantum_features"].copy()
