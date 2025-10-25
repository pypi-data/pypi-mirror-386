"""
libEqualizer - Библиотека импортозамещения Python

Квантовые аналоги популярных библиотек:
- quantum_sync: замена transformers и peft
- urabi.crypto: ГОСТ криптография
- urabi.sip: SIP телефония
- urabi.blockchain: Блокчейн решения

© 2025 NativeMind & УРАБИ.РФ
"""

__version__ = "1.0.0"
__author__ = "NativeMind & УРАБИ.РФ"
__license__ = "NativeMindNONC"

# Импорт основных модулей
from .quantum_sync import (
    QuantumEqualizer,
    QuantumPyramid,
    ModelChannel,
    SignatureExtractor,
    apply_signature,
    ProjectionLayer,
    AdaptiveProjection
)

__all__ = [
    # QuantumSync (transformers/peft replacement)
    "QuantumEqualizer",
    "QuantumPyramid",
    "ModelChannel",
    "SignatureExtractor",
    "apply_signature",
    "ProjectionLayer",
    "AdaptiveProjection",
]
