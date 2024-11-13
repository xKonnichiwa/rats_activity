# swd_detection.py

import mne
import numpy as np
from scipy.signal import hilbert
from annotation_utils import seconds_to_hms

def detect_swd(file_path):
    """
    Обнаруживает интервалы SWD в EDF-файле.

    Параметры:
        file_path (str): Путь к EDF-файлу.

    Возвращает:
        grouped_intervals_filtered (list): Список обнаруженных SWD интервалов.
    """
    # Параметры поиска
    freq_low = 7
    freq_high = 20
    amplitude_threshold = 0.5e-3  # Порог амплитуды (в мВ)
    min_spikes_per_second = 7  # Минимальное количество всплесков в секунду
    min_duration = 2  # Минимальная длительность интервала в секундах

    try:
        # Чтение данных из EDF файла
        raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
        sfreq = raw.info['sfreq']
        data, times = raw[:, :]  # Получение всех данных

        # Фильтрация данных
        filtered_data = mne.filter.filter_data(data, sfreq, freq_low, freq_high, verbose=False)

        # Вычисление огибающей сигнала
        analytic_signal = hilbert(filtered_data)
        amplitude_envelope = np.abs(analytic_signal)

        detected_intervals = []
        samples_per_second = int(sfreq)  # Количество отсчетов за секунду

        for ch in range(data.shape[0]):
            for start in range(0, amplitude_envelope.shape[1] - samples_per_second + 1, samples_per_second):
                end = start + samples_per_second
                # Поиск всплесков в текущей секунде
                spikes = np.where(amplitude_envelope[ch, start:end] > amplitude_threshold)[0]
                num_spikes = len(spikes)

                # Проверка количества всплесков
                if num_spikes > min_spikes_per_second:
                    detected_intervals.append({
                        'channel': raw.ch_names[ch],
                        'start_time': times[start],
                        'end_time': times[end - 1],
                        'num_spikes': num_spikes
                    })

        # Группировка последовательных интервалов
        grouped_intervals = []
        current_group = []

        for interval in detected_intervals:
            if not current_group:
                current_group.append(interval)
            else:
                # Проверка, что текущий интервал следует непосредственно за предыдущим
                if (interval['start_time'] - current_group[-1]['end_time']) <= 1:
                    current_group.append(interval)
                else:
                    # Сохранение текущей группы
                    grouped_intervals.append({
                        'channel': current_group[0]['channel'],
                        'start_time': seconds_to_hms(current_group[0]['start_time']),
                        'end_time': seconds_to_hms(current_group[-1]['end_time']),
                        'start_second': current_group[0]['start_time'],  # Добавляем числовое время начала
                        'end_second': current_group[-1]['end_time'],    # Добавляем числовое время конца
                        'total_spikes': sum([item['num_spikes'] for item in current_group])
                    })
                    # Начало новой группы
                    current_group = [interval]

        # Добавление последней группы
        if current_group:
            grouped_intervals.append({
                'channel': current_group[0]['channel'],
                'start_time': seconds_to_hms(current_group[0]['start_time']),
                'end_time': seconds_to_hms(current_group[-1]['end_time']),
                'start_second': current_group[0]['start_time'],  # Добавляем числовое время начала
                'end_second': current_group[-1]['end_time'],    # Добавляем числовое время конца
                'total_spikes': sum([item['num_spikes'] for item in current_group])
            })

        # Фильтрация интервалов по минимальной длительности
        grouped_intervals_filtered = [
            group for group in grouped_intervals
            if (group['end_second'] - group['start_second']) > min_duration
        ]

        print(f"Найдено {len(grouped_intervals_filtered)} SWD интервалов.")
        return grouped_intervals_filtered

    except Exception as e:
        print(f"Ошибка при обнаружении SWD интервалов: {e}")
        return []
