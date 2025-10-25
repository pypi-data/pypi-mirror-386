"""
Quantum Sync - Библиотека квантовой синхронизации AI моделей

Аналог transformers и peft, но для метода "Учитель-Ученик"

Основные компоненты:
- QuantumEqualizer: 4-канальный эквалайзер моделей
- QuantumPyramid: Пирамидальная синхронизация

© 2025 NativeMind - Квантовая Педагогика AI
"""

__version__ = "1.0.0"
__author__ = "NativeMind"
__license__ = "NativeMindNONC"

from .equalizer import QuantumEqualizer
from .pyramid import QuantumPyramid
from .signature import SignatureExtractor, apply_signature
from .projection import ProjectionLayer, AdaptiveProjection

__all__ = [
    "QuantumEqualizer",
    "QuantumPyramid",
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

