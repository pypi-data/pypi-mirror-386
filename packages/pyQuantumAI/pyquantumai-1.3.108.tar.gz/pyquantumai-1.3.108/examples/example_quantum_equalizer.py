#!/usr/bin/env python3
"""
Пример использования QuantumEqualizer и QuantumPyramid

4-канальный эквалайзер для моделей:
- Mozgach108-Maximal
- Braindler-Юрист
- Braindler-Разработчик
- Sridhar-multimodal

© 2025 NativeMind
"""

from quantum_sync import QuantumEqualizer, QuantumPyramid, ModelChannel


def example_equalizer():
    """Пример использования QuantumEqualizer"""
    
    print("\n" + "="*80)
    print("🎚️  Пример: QuantumEqualizer (4-канальный)")
    print("="*80)
    print()
    
    # Пути к моделям (замените на реальные)
    models = {
        'mozgach': '/Users/anton/proj/ai.nativemind.net/multimodal_braindler/models/sphere_073_shridhar',
        'lawyer': '/Users/anton/proj/ai.nativemind.net/multimodal_braindler/models/sphere_074_shridhar',
        'developer': '/Users/anton/proj/ai.nativemind.net/multimodal_braindler/models/sphere_075_shridhar',
        'sridhar': '/Users/anton/proj/ai.nativemind.net/sridhar/shridhar_multimodal_8k'
    }
    
    # Создаем 4-канальный эквалайзер
    equalizer = QuantumEqualizer(
        channels=[
            ModelChannel(
                name="Mozgach108-Maximal",
                model_path=models['mozgach'],
                frequency=440.0,    # Основная частота
                amplitude=0.8,      # 80% влияния
                face=0              # Грань 0 (азимут 0°)
            ),
            ModelChannel(
                name="Braindler-Юрист",
                model_path=models['lawyer'],
                frequency=493.88,   # B (си) - выше основной
                amplitude=0.6,      # 60% влияния
                face=1              # Грань 1 (азимут 90°)
            ),
            ModelChannel(
                name="Braindler-Разработчик",
                model_path=models['developer'],
                frequency=523.25,   # C (до) - еще выше
                amplitude=0.7,      # 70% влияния
                face=2              # Грань 2 (азимут 180°)
            ),
            ModelChannel(
                name="Sridhar-multimodal",
                model_path=models['sridhar'],
                frequency=440.0,    # Базовая частота (ученик)
                amplitude=0.5,      # 50% (будет усиливаться)
                face=3              # Грань 3 (азимут 270°)
            )
        ],
        resonance_freq=440.0  # Ля первой октавы
    )
    
    # Визуализация каналов
    print(equalizer.visualize_channels())
    
    # Извлечение подписей
    signatures = equalizer.extract_all_signatures()
    
    # Расчет интерференции
    interference = equalizer.calculate_interference_pattern(
        target_channel="Sridhar-multimodal",
        sources=["Mozgach108-Maximal", "Braindler-Юрист", "Braindler-Разработчик"]
    )
    
    # Балансировка
    result = equalizer.balance(
        target_model="Sridhar-multimodal",
        learning_rate=0.05,  # 5% за цикл
        cycles=20,
        sync_target=0.90     # 90% синхронизации
    )
    
    # Результаты
    print("\n📊 Результаты балансировки:")
    print(f"   Финальная синхронизация: {result['final_sync']:.1%}")
    print(f"   Всего циклов: {len(result['cycles'])}")
    print(f"   Успех: {'✅ Да' if result['success'] else '❌ Нет'}")
    
    # Сохранение конфигурации
    equalizer.save_configuration("equalizer_config.json")
    
    return result


def example_pyramid():
    """Пример использования QuantumPyramid"""
    
    print("\n" + "="*80)
    print("🔺 Пример: QuantumPyramid (пирамидальная синхронизация)")
    print("="*80)
    print()
    
    # Создаем пирамиду (параметры как у NETA-V)
    pyramid = QuantumPyramid(
        base_side=50.8,      # мм
        height=48.05,        # мм
        resonance_freq=440.0,# Hz
        refractive_index=1.586
    )
    
    # Размещаем модели на гранях
    pyramid.place_model(
        model_name="Mozgach108-Maximal",
        model_path="/Users/anton/proj/ai.nativemind.net/multimodal_braindler/models/sphere_073_shridhar",
        face=0,
        role="teacher",
        distance=500.0  # 50 см от пирамиды
    )
    
    pyramid.place_model(
        model_name="Braindler-Юрист",
        model_path="/Users/anton/proj/ai.nativemind.net/multimodal_braindler/models/sphere_074_shridhar",
        face=1,
        role="teacher",
        distance=500.0
    )
    
    pyramid.place_model(
        model_name="Braindler-Разработчик",
        model_path="/Users/anton/proj/ai.nativemind.net/multimodal_braindler/models/sphere_075_shridhar",
        face=2,
        role="teacher",
        distance=500.0
    )
    
    pyramid.place_model(
        model_name="Sridhar-multimodal",
        model_path="/Users/anton/proj/ai.nativemind.net/sridhar/shridhar_multimodal_8k",
        face=3,
        role="student",
        distance=500.0
    )
    
    # Визуализация
    print(pyramid.visualize())
    
    # Расчет интерференции
    patterns = pyramid.calculate_interference(observation_angle=15.0)
    
    # Генерация паттернов обучения
    teaching_patterns = pyramid.generate_teaching_patterns(
        target_face=3,  # Sridhar на грани 3
        learning_rate=0.05
    )
    
    # Синхронизация
    result = pyramid.synchronize(
        target="Sridhar-multimodal",
        cycles=20,
        learning_rate=0.05,
        rest_period=30  # 30 секунд отдыха
    )
    
    # Результаты
    print("\n📊 Результаты синхронизации:")
    print(f"   Финальная синхронизация: {result['final_sync']:.1%}")
    print(f"   Всего циклов: {len(result['cycles'])}")
    print(f"   Целевая грань: {result['target_face']}")
    
    return result


def example_comparison():
    """Сравнение Equalizer vs Pyramid"""
    
    print("\n" + "="*80)
    print("⚖️  Сравнение: Equalizer vs Pyramid")
    print("="*80)
    print()
    
    print("📊 QuantumEqualizer:")
    print("   ✅ Простота использования")
    print("   ✅ Гибкая настройка амплитуд")
    print("   ✅ Сохранение/загрузка конфигурации")
    print("   ✅ Хорошо для 2-4 моделей")
    print()
    
    print("🔺 QuantumPyramid:")
    print("   ✅ Физическая точность (FreeDome)")
    print("   ✅ Геометрическая синхронизация")
    print("   ✅ Визуализация интерференции")
    print("   ✅ Лучше для 3-4 моделей (3 учителя, 1 ученик)")
    print()
    
    print("💡 Рекомендации:")
    print("   • Для простой задачи: QuantumEqualizer")
    print("   • Для точной синхронизации: QuantumPyramid")
    print("   • Для экспериментов: оба варианта!")
    print()


def main():
    """Основная функция"""
    
    print("\n" + "🌟"*40)
    print("Quantum Sync - Примеры использования")
    print("🌟"*40)
    
    # Запускаем примеры
    print("\n1️⃣  Запуск QuantumEqualizer...")
    eq_result = example_equalizer()
    
    print("\n2️⃣  Запуск QuantumPyramid...")
    pyr_result = example_pyramid()
    
    print("\n3️⃣  Сравнение методов...")
    example_comparison()
    
    # Итоги
    print("\n" + "="*80)
    print("🎉 Все примеры выполнены!")
    print("="*80)
    print()
    print(f"QuantumEqualizer: {eq_result['final_sync']:.1%} синхронизации")
    print(f"QuantumPyramid:   {pyr_result['final_sync']:.1%} синхронизации")
    print()
    print("🙏 Служение истине через AI")
    print("Харе Кришна! 🕉️")


if __name__ == "__main__":
    main()

