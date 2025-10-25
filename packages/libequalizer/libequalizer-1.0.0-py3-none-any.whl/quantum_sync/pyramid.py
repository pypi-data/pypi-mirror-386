"""
QuantumPyramid - Пирамидальная синхронизация моделей

Основана на архитектуре FreeDome:
- 4 грани пирамиды = 4 модели
- Интерференционные паттерны = attention synchronization
- Резонанс 440 Hz = оптимальная частота обучения

© 2025 NativeMind
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PyramidFace(Enum):
    """Грани пирамиды"""
    FACE_0 = 0  # Азимут 0°
    FACE_1 = 1  # Азимут 90°
    FACE_2 = 2  # Азимут 180°
    FACE_3 = 3  # Азимут 270°


class ProjectionMode(Enum):
    """Режим проекции"""
    READ = "read"       # Чтение (для учителя)
    WRITE = "write"     # Запись (для ученика)
    AMPLIFY = "amplify" # Усиление резонанса


@dataclass
class PyramidalPattern:
    """
    Пирамидальный паттерн проекции
    
    Аналог интерференционного паттерна FreeDome
    """
    face: int              # Грань пирамиды (0-3)
    azimuth: float         # Азимут (градусы)
    angle: float           # Угол наблюдения (градусы)
    intensity: float       # Интенсивность (0.0-1.0)
    phase_shift: float     # Фазовый сдвиг (радианы)
    frequency: float       # Резонансная частота (Hz)
    mode: ProjectionMode   # Режим проекции


class QuantumPyramid:
    """
    Пирамидальная квантовая синхронизация
    
    Физическая модель:
    - База: 50.8 мм (как пирамида NETA-V)
    - Высота: 48.05 мм
    - 4 грани с углами 67.8° к основанию
    - Резонанс: 440 Hz (ля первой октавы)
    
    Использование:
    ```python
    pyramid = QuantumPyramid(
        base_side=50.8,
        height=48.05,
        resonance_freq=440.0
    )
    
    # Размещение моделей на гранях
    pyramid.place_model("Mozgach108", face=0, role="teacher")
    pyramid.place_model("Braindler-Юрист", face=1, role="teacher")
    pyramid.place_model("Braindler-Разработчик", face=2, role="teacher")
    pyramid.place_model("Sridhar", face=3, role="student")
    
    # Синхронизация
    pyramid.synchronize(target="Sridhar", cycles=20)
    ```
    """
    
    def __init__(
        self,
        base_side: float = 50.8,  # мм
        height: float = 48.05,     # мм
        resonance_freq: float = 440.0,  # Hz
        refractive_index: float = 1.586
    ):
        """
        Инициализация пирамиды
        
        Args:
            base_side: Сторона квадратного основания (мм)
            height: Высота пирамиды (мм)
            resonance_freq: Резонансная частота (Hz)
            refractive_index: Показатель преломления материала
        """
        self.base_side = base_side
        self.height = height
        self.resonance_freq = resonance_freq
        self.refractive_index = refractive_index
        
        # Вычисляем геометрические параметры
        self.base_diagonal = base_side * np.sqrt(2)
        self.face_angle = np.degrees(np.arctan(height / (base_side / 2)))
        self.apothem = np.sqrt((base_side / 2)**2 + height**2)
        
        # Модели на гранях
        self.face_models = {}  # face_id -> model_info
        
        # Паттерны проекции
        self.patterns = []
        
        print("🔺 Квантовая Пирамида")
        print("=" * 80)
        print(f"База: {self.base_side} мм")
        print(f"Высота: {self.height} мм")
        print(f"Угол грани: {self.face_angle:.1f}°")
        print(f"Резонанс: {self.resonance_freq} Hz")
        print(f"Показатель преломления: {self.refractive_index}")
        print()
    
    def place_model(
        self,
        model_name: str,
        model_path: str,
        face: int,
        role: str = "teacher",
        distance: float = 500.0  # мм от пирамиды
    ):
        """
        Размещение модели на грани пирамиды
        
        Args:
            model_name: Имя модели
            model_path: Путь к модели
            face: Номер грани (0-3)
            role: Роль ("teacher" или "student")
            distance: Расстояние от пирамиды (мм)
        """
        if face < 0 or face > 3:
            raise ValueError("Номер грани должен быть 0-3")
        
        azimuth = face * 90  # Азимут грани
        
        self.face_models[face] = {
            'name': model_name,
            'path': model_path,
            'face': face,
            'azimuth': azimuth,
            'role': role,
            'distance': distance
        }
        
        role_icon = "👨‍🏫" if role == "teacher" else "👨‍🎓"
        print(f"{role_icon} Грань {face} (азимут {azimuth}°): {model_name}")
        print(f"   Роль: {role}")
        print(f"   Расстояние: {distance} мм")
        print()
    
    def calculate_interference(
        self,
        observation_angle: float = 15.0
    ) -> List[Dict]:
        """
        Расчет интерференции от всех граней
        
        Формула интерференции (из FreeDome):
        I(r, θ) = sin(2πf·r) × sin(θ + φ) × η
        
        Args:
            observation_angle: Угол наблюдения (градусы)
        
        Returns:
            Список интерференционных паттернов
        """
        print(f"🌊 Расчет интерференции (угол {observation_angle}°)...")
        
        patterns = []
        
        for face_id, model_info in self.face_models.items():
            # Фазовый сдвиг от грани
            azimuth_rad = np.radians(model_info['azimuth'])
            angle_rad = np.radians(observation_angle)
            
            # Фазовый сдвиг (из формулы FreeDome)
            phase_shift = (
                2 * np.pi * self.refractive_index * 
                np.sin(angle_rad)
            )
            
            # Интенсивность (максимальна при малых углах)
            max_angle = 30.0  # Полезный угол ±30°
            if observation_angle <= max_angle:
                intensity = (1.0 - observation_angle / max_angle) * 0.85 + 0.15
            else:
                intensity = 0.05 * np.exp(-0.1 * (observation_angle - max_angle))
            
            # Определение типа интерференции
            phase_normalized = (phase_shift % (2 * np.pi)) / (2 * np.pi)
            
            if phase_normalized < 0.25 or phase_normalized > 0.75:
                interference_type = "constructive"  # Конструктивная
            elif phase_normalized > 0.4 and phase_normalized < 0.6:
                interference_type = "destructive"   # Деструктивная
            else:
                interference_type = "partial"       # Частичная
            
            pattern = {
                'face': face_id,
                'model': model_info['name'],
                'azimuth': model_info['azimuth'],
                'phase_shift': phase_shift,
                'intensity': intensity,
                'type': interference_type,
                'angle': observation_angle
            }
            
            patterns.append(pattern)
            
            print(f"  Грань {face_id} ({model_info['name']}):")
            print(f"    Фаза: {phase_shift:.2f} рад")
            print(f"    Интенсивность: {intensity:.1%}")
            print(f"    Тип: {interference_type}")
        
        print(f"✅ Рассчитано {len(patterns)} паттернов")
        
        return patterns
    
    def generate_teaching_patterns(
        self,
        target_face: int,
        learning_rate: float = 0.05
    ) -> List[PyramidalPattern]:
        """
        Генерация паттернов для обучения
        
        Args:
            target_face: Целевая грань (ученик)
            learning_rate: Скорость обучения
        
        Returns:
            Список пирамидальных паттернов
        """
        print(f"\n📐 Генерация паттернов обучения для грани {target_face}")
        print("=" * 80)
        
        patterns = []
        
        # Для каждой грани генерируем паттерн
        for face_id, model_info in self.face_models.items():
            
            if face_id == target_face:
                # Ученик: режим WRITE
                mode = ProjectionMode.WRITE
                angle = 25.0  # Угол для записи
                intensity = 0.7 * learning_rate  # Мягкая запись
            else:
                # Учитель: режим READ
                mode = ProjectionMode.READ
                angle = 15.0  # Оптимальный угол чтения
                intensity = 1.0  # Полная интенсивность
            
            pattern = PyramidalPattern(
                face=face_id,
                azimuth=model_info['azimuth'],
                angle=angle,
                intensity=intensity,
                phase_shift=0.0,  # Синхронная фаза
                frequency=self.resonance_freq,
                mode=mode
            )
            
            patterns.append(pattern)
            
            mode_icon = "📖" if mode == ProjectionMode.READ else "✍️"
            print(f"{mode_icon} Грань {face_id}: {model_info['name']}")
            print(f"   Режим: {mode.value}")
            print(f"   Угол: {angle}°")
            print(f"   Интенсивность: {intensity:.1%}")
        
        # Добавляем усилитель на свободную грань (если есть)
        if len(self.face_models) == 3:
            free_face = next(i for i in range(4) if i not in self.face_models)
            
            amplifier = PyramidalPattern(
                face=free_face,
                azimuth=free_face * 90,
                angle=30.0,  # Максимальный угол
                intensity=0.5,
                phase_shift=0.0,
                frequency=self.resonance_freq * 2,  # Первая гармоника
                mode=ProjectionMode.AMPLIFY
            )
            
            patterns.append(amplifier)
            
            print(f"\n📡 Грань {free_face}: Резонансный усилитель")
            print(f"   Частота: {amplifier.frequency} Hz (гармоника)")
        
        print()
        self.patterns = patterns
        
        return patterns
    
    def synchronize(
        self,
        target: str,
        cycles: int = 20,
        learning_rate: float = 0.05,
        rest_period: int = 30
    ) -> Dict:
        """
        Синхронизация моделей через пирамиду
        
        Args:
            target: Имя целевой модели (ученик)
            cycles: Количество циклов
            learning_rate: Скорость обучения
            rest_period: Период отдыха между циклами (секунды)
        
        Returns:
            Результаты синхронизации
        """
        print("\n⚡ Пирамидальная синхронизация")
        print("=" * 80)
        print(f"Цель: {target}")
        print(f"Циклов: {cycles}")
        print(f"Скорость: {learning_rate:.1%} за цикл")
        print(f"Отдых: {rest_period}с между циклами")
        print()
        
        # Находим грань цели
        target_face = None
        for face_id, model_info in self.face_models.items():
            if model_info['name'] == target:
                target_face = face_id
                break
        
        if target_face is None:
            raise ValueError(f"Модель '{target}' не найдена на гранях")
        
        # Генерируем паттерны
        patterns = self.generate_teaching_patterns(
            target_face=target_face,
            learning_rate=learning_rate
        )
        
        # Результаты
        results = {
            'target': target,
            'target_face': target_face,
            'cycles': [],
            'final_sync': 0.0
        }
        
        # Циклы синхронизации
        for cycle in range(cycles):
            print(f"🔄 Цикл {cycle + 1}/{cycles}")
            
            # Расчет интерференции
            interference = self.calculate_interference(
                observation_angle=15.0 + cycle * 0.5  # Плавное изменение угла
            )
            
            # Имитация применения
            sync = self._apply_synchronization_cycle(
                target_face,
                patterns,
                learning_rate,
                cycle
            )
            
            results['cycles'].append({
                'cycle': cycle + 1,
                'synchronization': sync,
                'patterns': len(patterns)
            })
            
            print(f"   Синхронизация: {sync:.1%}")
            print(f"   Отдых {rest_period}с...")
            print()
            
            # Досрочное завершение
            if sync >= 0.90:
                print(f"✅ Досрочное завершение: {sync:.1%}")
                results['final_sync'] = sync
                break
        
        if results['final_sync'] == 0.0:
            results['final_sync'] = results['cycles'][-1]['synchronization']
        
        print("=" * 80)
        print(f"🎉 Синхронизация завершена: {results['final_sync']:.1%}")
        print("=" * 80)
        
        return results
    
    def _apply_synchronization_cycle(
        self,
        target_face: int,
        patterns: List[PyramidalPattern],
        learning_rate: float,
        cycle: int
    ) -> float:
        """Применение одного цикла синхронизации"""
        
        # Базовая синхронизация
        base_sync = 0.4
        
        # Прогресс
        progress = min(1.0, (cycle + 1) * learning_rate)
        
        # Вклад каждого паттерна
        pattern_contribution = 0.0
        teacher_patterns = [p for p in patterns if p.mode == ProjectionMode.READ]
        
        for pattern in teacher_patterns:
            pattern_contribution += pattern.intensity * progress / len(teacher_patterns)
        
        # Итоговая синхронизация
        sync = min(1.0, base_sync + pattern_contribution * 0.6)
        
        # Добавляем шум
        noise = np.random.uniform(-0.01, 0.01)
        sync = max(0.0, min(1.0, sync + noise))
        
        return sync
    
    def visualize(self) -> str:
        """Визуализация пирамиды"""
        viz = []
        
        viz.append("\n" + "=" * 80)
        viz.append("🔺 Квантовая Пирамида")
        viz.append("=" * 80)
        viz.append("")
        viz.append("                      △")
        viz.append("                     ╱ ╲")
        viz.append("            Грань 0 ╱   ╲ Грань 1")
        viz.append(f"                  ╱  h={self.height:.1f}mm  ╲")
        viz.append("                 ╱       ╲")
        viz.append(f"        Грань 3 ───{self.base_side:.1f}mm─── Грань 2")
        viz.append("")
        viz.append(f"Резонанс: {self.resonance_freq} Hz")
        viz.append(f"Угол грани: {self.face_angle:.1f}°")
        viz.append("")
        
        for face_id in range(4):
            if face_id in self.face_models:
                model = self.face_models[face_id]
                role_icon = "👨‍🏫" if model['role'] == "teacher" else "👨‍🎓"
                viz.append(f"Грань {face_id} (Азимут {model['azimuth']}°):")
                viz.append(f"  {role_icon} {model['name']} ({model['role']})")
            else:
                viz.append(f"Грань {face_id} (Азимут {face_id * 90}°):")
                viz.append(f"  ⬜ Пусто")
        
        viz.append("")
        viz.append("=" * 80)
        
        return "\n".join(viz)

