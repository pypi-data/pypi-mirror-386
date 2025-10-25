#!/usr/bin/env python3
"""
Setup script for libEqualizer
© 2025 NativeMind & УРАБИ.РФ
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="libequalizer",
    version="1.0.0",
    author="NativeMind & УРАБИ.РФ",
    author_email="info@ураби.рф",
    description="Квантовая синхронизация AI моделей - отечественная замена transformers и peft",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/antondodonov/libEqualizer",
    project_urls={
        "Bug Tracker": "https://gitlab.com/antondodonov/libEqualizer/issues",
        "Documentation": "https://gitlab.com/antondodonov/libEqualizer/wiki",
        "Source Code": "https://gitlab.com/antondodonov/libEqualizer",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=1.13.0",
        "numpy>=1.21.0",
        "transformers>=4.30.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "crypto": [
            "cryptography>=41.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quantum-sync=quantum_sync.cli:main",
        ],
    },
    keywords=[
        "ai",
        "machine-learning",
        "quantum-computing",
        "model-synchronization",
        "transformers",
        "peft",
        "import-substitution",
        "russian-ai",
    ],
    license="NativeMindNONC",
    include_package_data=True,
    zip_safe=False,
)

