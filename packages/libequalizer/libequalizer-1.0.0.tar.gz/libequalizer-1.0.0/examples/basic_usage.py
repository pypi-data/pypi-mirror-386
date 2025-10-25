#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример использования библиотек импортозамещения

Демонстрирует основные возможности:
- NativeMind AI/ML библиотеки
- УРАБИ криптографические решения
- Общие компоненты
"""

import sys
import os

# Добавляем путь к исходному коду
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def demo_nativemind():
    """Демонстрация возможностей NativeMind"""
    print("🚀 Демонстрация NativeMind AI/ML библиотек")
    print("=" * 50)
    
    try:
        from nativemind.ai import PyTorchReplacement, get_module_info
        
        # Получение информации о модуле
        info = get_module_info()
        print(f"Модуль: {info['name']}")
        print(f"Описание: {info['description']}")
        print(f"Версия: {info['version']}")
        
        # Создание экземпляра PyTorch Replacement
        torch_repl = PyTorchReplacement(quantum_enabled=True)
        print(f"\nPyTorch Replacement создан:")
        print(f"  - Устройство: {torch_repl.device}")
        print(f"  - Квантовые алгоритмы: {'Включены' if torch_repl.quantum_enabled else 'Отключены'}")
        print(f"  - Российские оптимизации: {'Включены' if torch_repl.russian_optimizations else 'Отключены'}")
        
        # Создание тензоров
        tensor1 = torch_repl.tensor([1, 2, 3, 4, 5])
        tensor2 = torch_repl.tensor([10, 20, 30, 40, 50])
        
        print(f"\nСозданы тензоры:")
        print(f"  - Tensor 1: {tensor1}")
        print(f"  - Tensor 2: {tensor2}")
        
        # Операции с тензорами
        result = tensor1 + tensor2
        print(f"  - Сложение: {result}")
        
        result = tensor1 * tensor2
        print(f"  - Умножение: {result}")
        
        # Информация об устройстве
        device_info = torch_repl.get_device_info()
        print(f"\nИнформация об устройстве:")
        for key, value in device_info.items():
            print(f"  - {key}: {value}")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта NativeMind: {e}")
    except Exception as e:
        print(f"❌ Ошибка в NativeMind: {e}")

def demo_urabi():
    """Демонстрация возможностей УРАБИ"""
    print("\n🔐 Демонстрация УРАБИ криптографических решений")
    print("=" * 50)
    
    try:
        from urabi.crypto import GOSTCrypto, get_module_info
        
        # Получение информации о модуле
        info = get_module_info()
        print(f"Модуль: {info['name']}")
        print(f"Описание: {info['description']}")
        print(f"Версия: {info['version']}")
        
        # Создание экземпляра ГОСТ криптографии
        gost = GOSTCrypto(quantum_enabled=True, russian_optimizations=True)
        print(f"\nГОСТ криптография создана:")
        print(f"  - Квантовая криптография: {'Включена' if gost.quantum_enabled else 'Отключена'}")
        print(f"  - Российские оптимизации: {'Включены' if gost.russian_optimizations else 'Отключены'}")
        
        # Поддерживаемые стандарты
        standards = gost.get_standards_info()
        print(f"\nПоддерживаемые стандарты:")
        for standard, description in standards.items():
            print(f"  - {standard}: {description}")
        
        # Генерация ключей
        private_key, public_key = gost.generate_key_pair(256)
        print(f"\nСгенерированы ключи:")
        print(f"  - Приватный ключ: {private_key.hex()[:32]}...")
        print(f"  - Публичный ключ: {public_key.hex()[:32]}...")
        
        # Подписание данных
        test_data = b"Тестовые данные для подписи"
        signature = gost.sign_data(test_data, private_key)
        print(f"\nПодписание данных:")
        print(f"  - Данные: {test_data.decode('utf-8')}")
        print(f"  - Подпись: {signature.hex()[:32]}...")
        
        # Проверка подписи
        is_valid = gost.verify_signature(test_data, signature, public_key)
        print(f"  - Подпись верна: {'Да' if is_valid else 'Нет'}")
        
        # Хеширование данных
        hash_result = gost.hash_data(test_data)
        print(f"\nХеширование данных:")
        print(f"  - Хеш: {hash_result.hex()}")
        
        # Шифрование данных
        encryption_key = gost.generate_random_bytes(32)
        encrypted = gost.encrypt_data(test_data, encryption_key, "ECB")
        decrypted = gost.decrypt_data(encrypted, encryption_key, "ECB")
        
        print(f"\nШифрование данных:")
        print(f"  - Исходные данные: {test_data.decode('utf-8')}")
        print(f"  - Зашифрованные: {encrypted.hex()[:32]}...")
        print(f"  - Расшифрованные: {decrypted.decode('utf-8')}")
        print(f"  - Расшифрование успешно: {'Да' if decrypted == test_data else 'Нет'}")
        
        # Статус квантовых компонентов
        quantum_status = gost.get_quantum_status()
        print(f"\nСтатус квантовых компонентов:")
        for key, value in quantum_status.items():
            print(f"  - {key}: {value}")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта УРАБИ: {e}")
    except Exception as e:
        print(f"❌ Ошибка в УРАБИ: {e}")

def demo_common():
    """Демонстрация общих компонентов"""
    print("\n🔧 Демонстрация общих компонентов")
    print("=" * 50)
    
    try:
        from common import get_module_info
        
        # Получение информации о модуле
        info = get_module_info()
        print(f"Модуль: {info['name']}")
        print(f"Описание: {info['description']}")
        print(f"Версия: {info['version']}")
        
        # Компоненты
        components = info['components']
        print(f"\nДоступные компоненты:")
        for component, description in components.items():
            print(f"  - {component}: {description}")
        
        # Возможности
        features = info['features']
        print(f"\nВозможности:")
        for feature in features:
            print(f"  - {feature}")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта общих компонентов: {e}")
    except Exception as e:
        print(f"❌ Ошибка в общих компонентах: {e}")

def main():
    """Основная функция демонстрации"""
    print("🇷🇺 Python Libraries Import Substitution - Демонстрация")
    print("Проект импортозамещения библиотек для NativeMind.ru и УРАБИ.РФ")
    print("=" * 70)
    
    # Демонстрация NativeMind
    demo_nativemind()
    
    # Демонстрация УРАБИ
    demo_urabi()
    
    # Демонстрация общих компонентов
    demo_common()
    
    print("\n" + "=" * 70)
    print("✅ Демонстрация завершена!")
    print("\nДля получения дополнительной информации:")
    print("  - NativeMind.ru: https://nativemind.ru")
    print("  - УРАБИ.РФ: https://ураби.рф")
    print("  - GitHub: https://github.com/nativemind/python-import-substitution")

if __name__ == "__main__":
    main()
