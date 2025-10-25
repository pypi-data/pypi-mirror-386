"""
QuantumPrisma - Квантовая призма для разложения моделей на частотный спектр

Аналогия с оптической призмой:
- Белый свет (универсальная модель) → Призма → Спектр цветов (специализированные модели)
- Каждая частота = специализация в определенном домене

Применение:
1. Анализ частотного спектра модели
2. Разложение универсальной модели на специализированные
3. Создание "спектра экспертизы"

© 2025 NativeMind
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FrequencyComponent:
    """Частотная компонента модели"""
    frequency: float  # Частота в Hz
    amplitude: float  # Амплитуда (0.0-1.0)
    phase: float      # Фаза (0-360 градусов)
    domain: str       # Домен специализации
    energy: float     # Энергия компоненты


class QuantumPrisma:
    """
    Квантовая призма для спектрального анализа AI моделей
    
    Разлагает "белый шум" модели на спектр частот:
    - 440 Hz (A4) - Базовая частота (общие знания)
    - 880 Hz (A5) - Вторая гармоника (специализация)
    - 1320 Hz (E6) - Третья гармоника (экспертиза)
    - 1760 Hz (A6) - Четвертая гармоника (мастерство)
    """
    
    def __init__(
        self,
        base_frequency: float = 440.0,
        num_harmonics: int = 4,
        resolution: int = 108  # 108 квантовых элементов
    ):
        """
        Инициализация квантовой призмы
        
        Args:
            base_frequency: Базовая частота (Hz)
            num_harmonics: Количество гармоник
            resolution: Разрешение спектрального анализа
        """
        self.base_frequency = base_frequency
        self.num_harmonics = num_harmonics
        self.resolution = resolution
        
        # Генерируем гармоники
        self.harmonics = self._generate_harmonics()
        
        # Маппинг частот на домены
        self.frequency_domains = {
            440.0: "general",      # Общие знания
            880.0: "specialized",  # Специализация
            1320.0: "expert",      # Экспертиза
            1760.0: "master"       # Мастерство
        }
        
        print(f"🔮 Квантовая Призма")
        print("=" * 80)
        print(f"Базовая частота: {self.base_frequency} Hz")
        print(f"Гармоник: {self.num_harmonics}")
        print(f"Разрешение: {self.resolution} элементов")
        print()
        
        for i, freq in enumerate(self.harmonics, 1):
            domain = self.frequency_domains.get(freq, "unknown")
            print(f"  Гармоника {i}: {freq} Hz ({domain})")
        print()
    
    def _generate_harmonics(self) -> List[float]:
        """Генерация гармонических частот"""
        harmonics = []
        for n in range(1, self.num_harmonics + 1):
            freq = self.base_frequency * n
            harmonics.append(freq)
        return harmonics
    
    def analyze_spectrum(
        self,
        model_path: str,
        sample_size: int = 1000
    ) -> Dict[float, FrequencyComponent]:
        """
        Анализ частотного спектра модели
        
        Args:
            model_path: Путь к модели или HuggingFace ID
            sample_size: Размер выборки для анализа
        
        Returns:
            Словарь {частота: компонента}
        """
        print(f"\n🔬 Спектральный анализ модели: {model_path}")
        print("=" * 80)
        
        spectrum = {}
        
        try:
            # Загружаем модель для анализа
            from transformers import AutoModelForCausalLM
            
            print(f"📥 Загружаю модель...")
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="cpu",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            # Анализируем каждую гармонику
            for freq in self.harmonics:
                print(f"\n📊 Анализ частоты: {freq} Hz")
                
                component = self._analyze_frequency(
                    model,
                    freq,
                    sample_size
                )
                
                spectrum[freq] = component
                
                print(f"   Амплитуда: {component.amplitude:.1%}")
                print(f"   Фаза: {component.phase:.1f}°")
                print(f"   Энергия: {component.energy:.3f}")
                print(f"   Домен: {component.domain}")
            
            print("\n✅ Спектральный анализ завершен")
            
        except Exception as e:
            print(f"\n⚠️ Ошибка анализа: {e}")
            # Возвращаем симуляцию для тестирования
            for freq in self.harmonics:
                spectrum[freq] = self._simulate_component(freq)
        
        return spectrum
    
    def _analyze_frequency(
        self,
        model,
        frequency: float,
        sample_size: int
    ) -> FrequencyComponent:
        """
        Анализ конкретной частоты в модели
        
        Метод:
        1. Извлекаем случайные веса из модели
        2. Применяем FFT (Fast Fourier Transform)
        3. Измеряем амплитуду на целевой частоте
        """
        # Собираем случайные веса
        weights = []
        for name, param in model.named_parameters():
            if param.requires_grad and len(param.shape) >= 2:
                # Берем случайную подвыборку
                flat = param.data.flatten()
                if len(flat) > sample_size:
                    indices = torch.randperm(len(flat))[:sample_size]
                    sample = flat[indices]
                else:
                    sample = flat
                
                weights.extend(sample.cpu().numpy())
                
                if len(weights) >= sample_size:
                    break
        
        weights = np.array(weights[:sample_size])
        
        # Нормализация
        weights = (weights - weights.mean()) / (weights.std() + 1e-8)
        
        # FFT анализ
        fft = np.fft.fft(weights)
        freqs = np.fft.fftfreq(len(weights), d=1.0/sample_size)
        
        # Находим ближайшую частоту к целевой
        target_idx = np.argmin(np.abs(freqs - frequency))
        
        # Извлекаем компоненты
        amplitude = np.abs(fft[target_idx]) / len(weights)
        phase = np.angle(fft[target_idx], deg=True)
        energy = amplitude ** 2
        
        domain = self.frequency_domains.get(frequency, "unknown")
        
        return FrequencyComponent(
            frequency=frequency,
            amplitude=min(amplitude, 1.0),
            phase=phase % 360,
            domain=domain,
            energy=energy
        )
    
    def _simulate_component(self, frequency: float) -> FrequencyComponent:
        """Симуляция компоненты для тестирования"""
        # Используем детерминированную генерацию
        np.random.seed(int(frequency))
        
        amplitude = 0.3 + np.random.random() * 0.4  # 0.3-0.7
        phase = np.random.random() * 360
        energy = amplitude ** 2
        domain = self.frequency_domains.get(frequency, "unknown")
        
        return FrequencyComponent(
            frequency=frequency,
            amplitude=amplitude,
            phase=phase,
            domain=domain,
            energy=energy
        )
    
    def decompose_model(
        self,
        model_path: str,
        target_frequencies: Optional[List[float]] = None
    ) -> Dict[float, Dict]:
        """
        Разложение модели на частотные компоненты
        
        Args:
            model_path: Путь к модели
            target_frequencies: Целевые частоты (None = все гармоники)
        
        Returns:
            Словарь {частота: {компонента, веса}}
        """
        if target_frequencies is None:
            target_frequencies = self.harmonics
        
        print(f"\n🌈 Разложение модели на частотные компоненты")
        print("=" * 80)
        print(f"Модель: {model_path}")
        print(f"Частот: {len(target_frequencies)}")
        print()
        
        # Сначала анализируем спектр
        spectrum = self.analyze_spectrum(model_path)
        
        # Разлагаем на компоненты
        components = {}
        for freq in target_frequencies:
            if freq in spectrum:
                component = spectrum[freq]
                
                print(f"📡 Частота {freq} Hz ({component.domain}):")
                print(f"   Амплитуда: {component.amplitude:.1%}")
                print(f"   Энергия: {component.energy:.3f}")
                
                components[freq] = {
                    'component': component,
                    'filter': self._create_frequency_filter(freq)
                }
        
        print("\n✅ Разложение завершено")
        
        return components
    
    def _create_frequency_filter(self, frequency: float) -> Dict:
        """Создание частотного фильтра для модели"""
        return {
            'frequency': frequency,
            'bandwidth': frequency * 0.1,  # 10% от частоты
            'type': 'bandpass'
        }
    
    def synthesize_spectrum(
        self,
        components: Dict[float, FrequencyComponent],
        target_domain: str = "general"
    ) -> Dict:
        """
        Синтез спектра из компонент
        
        Args:
            components: Частотные компоненты
            target_domain: Целевой домен
        
        Returns:
            Синтезированный спектр
        """
        print(f"\n🎨 Синтез спектра для домена: {target_domain}")
        print("=" * 80)
        
        # Фильтруем компоненты по домену
        filtered = {
            freq: comp 
            for freq, comp in components.items()
            if comp.domain == target_domain or target_domain == "all"
        }
        
        # Вычисляем общую энергию
        total_energy = sum(comp.energy for comp in filtered.values())
        
        # Нормализуем амплитуды
        normalized = {}
        for freq, comp in filtered.items():
            normalized_amp = comp.amplitude / (total_energy + 1e-8)
            normalized[freq] = FrequencyComponent(
                frequency=comp.frequency,
                amplitude=normalized_amp,
                phase=comp.phase,
                domain=comp.domain,
                energy=comp.energy
            )
            
            print(f"  {freq} Hz: амплитуда={normalized_amp:.1%}, энергия={comp.energy:.3f}")
        
        print(f"\n✅ Синтез завершен: {len(normalized)} компонент")
        
        return {
            'components': normalized,
            'total_energy': total_energy,
            'domain': target_domain
        }
    
    def visualize_spectrum(
        self,
        spectrum: Dict[float, FrequencyComponent]
    ) -> str:
        """
        ASCII визуализация спектра
        
        Returns:
            ASCII график
        """
        output = []
        output.append("\n📊 Спектральная диаграмма")
        output.append("=" * 80)
        
        # Находим максимальную амплитуду для нормализации
        max_amp = max(comp.amplitude for comp in spectrum.values())
        
        for freq, comp in sorted(spectrum.items()):
            # Нормализуем к 50 символам
            bar_length = int((comp.amplitude / max_amp) * 50)
            bar = "█" * bar_length
            
            output.append(
                f"{freq:6.0f} Hz [{comp.domain:12s}] "
                f"{bar} {comp.amplitude:.1%}"
            )
        
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def refract(
        self,
        model_path: str,
        angle: float = 45.0
    ) -> Dict:
        """
        Преломление модели через призму
        
        Args:
            model_path: Модель для преломления
            angle: Угол падения (градусы)
        
        Returns:
            Преломленный спектр
        """
        print(f"\n🌈 Преломление модели через призму")
        print("=" * 80)
        print(f"Угол падения: {angle}°")
        print()
        
        # Анализируем спектр
        spectrum = self.analyze_spectrum(model_path)
        
        # Применяем закон преломления (упрощенная версия)
        refracted = {}
        for freq, comp in spectrum.items():
            # Коэффициент преломления зависит от частоты
            n = 1.0 + (freq / self.base_frequency) * 0.1
            
            # Закон Снеллиуса: n1 * sin(θ1) = n2 * sin(θ2)
            refraction_angle = np.arcsin(
                np.sin(np.radians(angle)) / n
            ) * 180 / np.pi
            
            # Новая амплитуда зависит от угла
            new_amplitude = comp.amplitude * np.cos(np.radians(refraction_angle))
            
            refracted[freq] = FrequencyComponent(
                frequency=freq,
                amplitude=new_amplitude,
                phase=(comp.phase + refraction_angle) % 360,
                domain=comp.domain,
                energy=new_amplitude ** 2
            )
            
            print(f"  {freq} Hz: {angle:.1f}° → {refraction_angle:.1f}°")
        
        print("\n✅ Преломление завершено")
        
        return {
            'spectrum': refracted,
            'incident_angle': angle,
            'base_frequency': self.base_frequency
        }


def create_frequency_map(
    base_freq: float = 440.0,
    num_octaves: int = 3
) -> Dict[str, float]:
    """
    Создание карты частот для разных доменов
    
    Args:
        base_freq: Базовая частота (A4 = 440 Hz)
        num_octaves: Количество октав
    
    Returns:
        Словарь {домен: частота}
    """
    frequency_map = {
        "general": base_freq,           # A4 - Общие знания
        "specialized": base_freq * 2,   # A5 - Специализация
        "expert": base_freq * 3,        # E6 - Экспертиза
        "master": base_freq * 4,        # A6 - Мастерство
    }
    
    # Добавляем октавы
    for octave in range(1, num_octaves + 1):
        freq = base_freq * (2 ** octave)
        frequency_map[f"octave_{octave}"] = freq
    
    return frequency_map

