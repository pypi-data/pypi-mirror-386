"""
pyQuantumAI - Библиотека квантовой AI педагогики

ПОЛНЫЙ ЦИКЛ обучения через квантовый резонанс:
1. QuantumPrisma - Спектральный анализ моделей
2. QuantumEqualize - Синхронизация через резонанс
3. QuantumPyramid - Пирамидальная геометрия
4. QuantumRetrain - Полный цикл переобучения

Не классический fine-tuning, а КВАНТОВОЕ ПЕРЕОБУЧЕНИЕ!

© 2025 NativeMind - Квантовая Педагогика AI
"""

__version__ = "1.3.108"
__author__ = "NativeMind"
__license__ = "NativeMindNONC"

from .prisma import QuantumPrisma, FrequencyComponent, create_frequency_map
from .equalizer import QuantumEqualizer, ModelChannel
from .pyramid import QuantumPyramid
from .retrain import QuantumRetrain, quick_retrain
from .signature import SignatureExtractor, apply_signature
from .projection import ProjectionLayer, AdaptiveProjection

__all__ = [
    # Призма - Анализ
    "QuantumPrisma",
    "FrequencyComponent",
    "create_frequency_map",
    
    # Эквалайзер - Синхронизация
    "QuantumEqualizer",
    "ModelChannel",
    
    # Пирамида - Геометрия
    "QuantumPyramid",
    
    # Retrain - Полный цикл
    "QuantumRetrain",
    "quick_retrain",
    
    # Утилиты
    "SignatureExtractor",
    "apply_signature",
    "ProjectionLayer",
    "AdaptiveProjection",
]

# Версии совместимости
TRANSFORMERS_MIN_VERSION = "4.30.0"
PEFT_MIN_VERSION = "0.4.0"

# Константы
DEFAULT_LEARNING_RATE = 0.05  # 5% за цикл
DEFAULT_CYCLES = 20
DEFAULT_SYNC_TARGET = 0.90  # 90% синхронизации
RESONANCE_FREQUENCY = 440.0  # Hz (как FreeDome)

# Конфигурация FreeDome аналогии
FREEDOME_FACES = 4  # 4 грани пирамиды
FREEDOME_ANGLES = [0, 90, 180, 270]  # Азимуты граней
QUANTUM_ELEMENTS = 108  # Квантовые элементы

