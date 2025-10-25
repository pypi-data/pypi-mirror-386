"""
QuantumRetrain - Полный цикл квантового переобучения

Интегрирует все компоненты:
1. QuantumPrisma - Спектральный анализ
2. QuantumEqualize - Синхронизация
3. Retrain - Применение изменений

Это НЕ классический fine-tuning, а квантовое переобучение через резонанс!

© 2025 NativeMind
"""

import torch
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

from .prisma import QuantumPrisma, FrequencyComponent
from .equalizer import QuantumEqualizer, ModelChannel
from .pyramid import QuantumPyramid


class QuantumRetrain:
    """
    Полный цикл квантового переобучения
    
    Алгоритм:
    1. Анализ спектра учителей (QuantumPrisma)
    2. Синхронизация через резонанс (QuantumEqualize)
    3. Применение и сохранение (Retrain)
    """
    
    def __init__(
        self,
        base_frequency: float = 440.0,
        method: str = "equalizer"  # "equalizer" или "pyramid"
    ):
        """
        Инициализация квантового переобучения
        
        Args:
            base_frequency: Базовая частота (Hz)
            method: Метод синхронизации
        """
        self.base_frequency = base_frequency
        self.method = method
        
        # Компоненты
        self.prisma = QuantumPrisma(base_frequency=base_frequency)
        self.equalizer = None
        self.pyramid = None
        
        print(f"🔮 Квантовое Переобучение")
        print("=" * 80)
        print(f"Метод: {method}")
        print(f"Базовая частота: {base_frequency} Hz")
        print()
    
    def analyze_teachers(
        self,
        teacher_models: List[str]
    ) -> Dict[str, Dict[float, FrequencyComponent]]:
        """
        Шаг 1: Анализ спектра учителей
        
        Args:
            teacher_models: Список путей к моделям учителей
        
        Returns:
            Словарь {модель: {частота: компонента}}
        """
        print("\n" + "=" * 80)
        print("ШАГ 1: Анализ спектра учителей")
        print("=" * 80)
        
        spectra = {}
        for model_path in teacher_models:
            print(f"\n📊 Анализ учителя: {model_path}")
            spectrum = self.prisma.analyze_spectrum(model_path)
            spectra[model_path] = spectrum
            
            # Визуализация
            print(self.prisma.visualize_spectrum(spectrum))
        
        print("\n✅ Анализ всех учителей завершен")
        
        return spectra
    
    def prepare_synchronization(
        self,
        teacher_models: List[str],
        student_model: str,
        teacher_amplitudes: Optional[List[float]] = None
    ):
        """
        Шаг 2: Подготовка синхронизации
        
        Args:
            teacher_models: Учителя
            student_model: Ученик
            teacher_amplitudes: Амплитуды учителей (опционально)
        """
        print("\n" + "=" * 80)
        print("ШАГ 2: Подготовка синхронизации")
        print("=" * 80)
        
        # Устанавливаем амплитуды по умолчанию
        if teacher_amplitudes is None:
            # Линейно убывающие амплитуды
            teacher_amplitudes = [
                1.0 - (i * 0.1) 
                for i in range(len(teacher_models))
            ]
        
        if self.method == "equalizer":
            # Создаем каналы для эквалайзера
            channels = []
            
            # Учителя
            for i, (model, amp) in enumerate(zip(teacher_models, teacher_amplitudes)):
                channels.append(
                    ModelChannel(
                        name=f"Teacher-{i+1}",
                        model_path=model,
                        face=i,
                        amplitude=amp
                    )
                )
            
            # Ученик
            channels.append(
                ModelChannel(
                    name="Student",
                    model_path=student_model,
                    face=len(teacher_models),
                    amplitude=0.5
                )
            )
            
            self.equalizer = QuantumEqualizer(
                channels=channels,
                resonance_freq=self.base_frequency
            )
            
            print(f"\n✅ Эквалайзер готов: {len(channels)} каналов")
            
        elif self.method == "pyramid":
            # Создаем пирамиду
            from .pyramid import FREEDOME_BASE, FREEDOME_HEIGHT
            
            self.pyramid = QuantumPyramid(
                base_side=FREEDOME_BASE,
                height=FREEDOME_HEIGHT,
                resonance_freq=self.base_frequency
            )
            
            # Размещаем модели на гранях
            for i, model in enumerate(teacher_models):
                self.pyramid.place_model(
                    model_name=f"Teacher-{i+1}",
                    model_path=model,
                    face=i,
                    role="teacher"
                )
            
            # Ученик на последней грани
            self.pyramid.place_model(
                model_name="Student",
                model_path=student_model,
                face=len(teacher_models),
                role="student"
            )
            
            print(f"\n✅ Пирамида готова: {len(teacher_models)+1} моделей")
        
        else:
            raise ValueError(f"Неизвестный метод: {self.method}")
    
    def synchronize(
        self,
        cycles: int = 20,
        learning_rate: float = 0.05,
        auto_save: bool = True,
        save_mode: str = "lora"
    ) -> Dict:
        """
        Шаг 3: Синхронизация через резонанс
        
        Args:
            cycles: Количество циклов
            learning_rate: Скорость обучения
            auto_save: Автосохранение
            save_mode: Режим сохранения ("lora" или "full")
        
        Returns:
            Результаты синхронизации
        """
        print("\n" + "=" * 80)
        print("ШАГ 3: Синхронизация через резонанс")
        print("=" * 80)
        
        if self.method == "equalizer":
            result = self.equalizer.balance(
                target_model="Student",
                learning_rate=learning_rate,
                cycles=cycles,
                auto_save=auto_save,
                save_mode=save_mode
            )
        
        elif self.method == "pyramid":
            result = self.pyramid.synchronize(
                target="Student",
                cycles=cycles,
                learning_rate=learning_rate,
                auto_save=auto_save,
                save_mode=save_mode
            )
        
        else:
            raise ValueError(f"Неизвестный метод: {self.method}")
        
        print("\n✅ Синхронизация завершена")
        
        return result
    
    def full_retrain(
        self,
        teacher_models: List[str],
        student_model: str,
        teacher_amplitudes: Optional[List[float]] = None,
        cycles: int = 20,
        learning_rate: float = 0.05,
        auto_save: bool = True,
        save_mode: str = "lora",
        output_path: Optional[str] = None
    ) -> Dict:
        """
        ПОЛНЫЙ цикл квантового переобучения
        
        Выполняет все 3 шага:
        1. Анализ спектра
        2. Подготовка
        3. Синхронизация
        
        Args:
            teacher_models: Список учителей
            student_model: Ученик
            teacher_amplitudes: Амплитуды (опционально)
            cycles: Циклов синхронизации
            learning_rate: Скорость
            auto_save: Автосохранение
            save_mode: "lora" или "full"
            output_path: Путь для сохранения
        
        Returns:
            Полный отчет о переобучении
        """
        print("\n" + "=" * 80)
        print("🔥 ПОЛНЫЙ ЦИКЛ КВАНТОВОГО ПЕРЕОБУЧЕНИЯ")
        print("=" * 80)
        print(f"Учителей: {len(teacher_models)}")
        print(f"Ученик: {student_model}")
        print(f"Метод: {self.method}")
        print(f"Циклов: {cycles}")
        print(f"Скорость: {learning_rate:.1%}")
        print()
        
        # Шаг 1: Анализ спектра
        spectra = self.analyze_teachers(teacher_models)
        
        # Шаг 2: Подготовка
        self.prepare_synchronization(
            teacher_models,
            student_model,
            teacher_amplitudes
        )
        
        # Шаг 3: Синхронизация
        result = self.synchronize(
            cycles=cycles,
            learning_rate=learning_rate,
            auto_save=auto_save,
            save_mode=save_mode
        )
        
        # Итоговый отчет
        report = {
            'spectra': spectra,
            'synchronization': result,
            'method': self.method,
            'base_frequency': self.base_frequency,
            'teachers': len(teacher_models),
            'final_sync': result.get('final_sync', 0.0),
            'success': result.get('success', False)
        }
        
        # Сохранение отчета
        if output_path and auto_save:
            self._save_report(report, output_path)
        
        # Финальная визуализация
        self._print_final_report(report)
        
        return report
    
    def _save_report(self, report: Dict, output_path: str):
        """Сохранение отчета о переобучении"""
        import json
        
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = output_dir / "quantum_retrain_report.json"
        
        # Подготовка для JSON (убираем непереводимые объекты)
        json_report = {
            'method': report['method'],
            'base_frequency': report['base_frequency'],
            'teachers': report['teachers'],
            'final_sync': report['final_sync'],
            'success': report['success'],
            'synchronization': {
                'final_sync': report['synchronization'].get('final_sync', 0.0),
                'success': report['synchronization'].get('success', False),
                'cycles': len(report['synchronization'].get('cycles', []))
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Отчет сохранен: {report_file}")
    
    def _print_final_report(self, report: Dict):
        """Печать финального отчета"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 80)
        print()
        
        print(f"Метод: {report['method']}")
        print(f"Базовая частота: {report['base_frequency']} Hz")
        print(f"Учителей: {report['teachers']}")
        print()
        
        print(f"Финальная синхронизация: {report['final_sync']:.1%}")
        print(f"Успех: {'✅ Да' if report['success'] else '⚠️ Частично'}")
        print()
        
        if 'saved_path' in report['synchronization']:
            print(f"Модель сохранена: {report['synchronization']['saved_path']}")
            print(f"Режим: {report['synchronization'].get('save_mode', 'N/A')}")
        
        print()
        print("=" * 80)
        print("🎉 КВАНТОВОЕ ПЕРЕОБУЧЕНИЕ ЗАВЕРШЕНО!")
        print("=" * 80)


def quick_retrain(
    teachers: List[str],
    student: str,
    method: str = "equalizer",
    output: str = "./quantum_retrained"
) -> Dict:
    """
    Быстрое квантовое переобучение с настройками по умолчанию
    
    Args:
        teachers: Список учителей
        student: Ученик
        method: "equalizer" или "pyramid"
        output: Путь для сохранения
    
    Returns:
        Отчет о переобучении
    """
    retrain = QuantumRetrain(method=method)
    
    return retrain.full_retrain(
        teacher_models=teachers,
        student_model=student,
        cycles=20,
        learning_rate=0.05,
        auto_save=True,
        save_mode="lora",
        output_path=output
    )

