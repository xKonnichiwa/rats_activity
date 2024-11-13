# ds_detection.py

import mne
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
from .annotation_utils import time_to_seconds, seconds_to_hms

def detect_ds(file_path):
    """
    Обнаруживает интервалы DS в EDF-файле.

    Параметры:
        file_path (str): Путь к EDF-файлу.

    Возвращает:
        matching_seconds (list): Список обнаруженных DS интервалов.
    """
    # Параметры поиска
    cutoff = 8.0  # Порог частоты для низкочастотного фильтра
    order = 3
    min_peaks_per_sec = 1  # Минимальное количество пиков
    max_peaks_per_sec = 8  # Максимальное количество пиков
    lower_amplitude_threshold = 0.00008  # Нижний порог амплитуды
    upper_amplitude_threshold = 0.00030  # Верхний порог амплитуды
    min_duration = 7  # Минимальная длительность интервала в секундах

    try:
        # Загрузка EDF-файла
        raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
        # Выбор каналов (первые 3 или другие при необходимости)
        selected_channels = raw.ch_names[:3]  # Или укажите конкретные имена каналов
        raw.pick_channels(selected_channels)
        data = raw.get_data()
        sfreq = raw.info['sfreq']

        # Функция для сглаживания через фильтр низких частот
        def lowpass_filter(data, cutoff=8.0, fs=sfreq, order=3):
            nyquist = 0.5 * fs
            normal_cutoff = cutoff / nyquist
            b, a = butter(order, normal_cutoff, btype='low')
            y = filtfilt(b, a, data)
            return y

        # Применяем фильтр к каждому каналу
        smoothed_data = np.array([lowpass_filter(channel) for channel in data])

        matching_seconds = []
        current_interval = None  # Текущий интервал для всех каналов

        # Проходим по каждой секунде
        total_seconds = int(smoothed_data.shape[1] / sfreq)
        for sec in range(total_seconds):
            # Флаг, показывающий, удовлетворяет ли секунда условиям на всех каналах
            all_channels_match = True

            # Проверяем каждый канал в текущую секунду
            for channel_data in smoothed_data:
                # Выделяем данные для текущей секунды
                start_idx = int(sec * sfreq)
                end_idx = int((sec + 1) * sfreq)
                segment = channel_data[start_idx:end_idx]

                # Ищем все пики (всплески) выше минимального порога
                peaks, properties = find_peaks(segment, height=lower_amplitude_threshold)

                # Проверяем, что количество пиков в пределах от min_peaks_per_sec до max_peaks_per_sec
                if len(peaks) < min_peaks_per_sec or len(peaks) > max_peaks_per_sec:
                    all_channels_match = False
                    break

                # Проверяем, что хотя бы один пик не превышает верхний порог
                peak_heights = properties['peak_heights']
                if np.any(peak_heights > upper_amplitude_threshold):
                    all_channels_match = False
                    break

            # Если секунда удовлетворяет условиям на всех каналах
            if all_channels_match:
                if current_interval is None:
                    # Начинаем новый интервал
                    current_interval = {'start_second': sec, 'end_second': sec}
                else:
                    # Продолжаем текущий интервал
                    current_interval['end_second'] = sec
            else:
                # Завершаем текущий интервал и сохраняем, если длительность >= min_duration
                if current_interval is not None:
                    if (current_interval['end_second'] - current_interval['start_second'] + 1) >= min_duration:
                        matching_seconds.append({
                            'start_second': current_interval['start_second'],
                            'start_time': seconds_to_hms(current_interval['start_second']),
                            'end_second': current_interval['end_second'],
                            'end_time': seconds_to_hms(current_interval['end_second']),
                            'duration_seconds': current_interval['end_second'] - current_interval['start_second'] + 1
                        })
                    current_interval = None

        # Добавляем последний интервал, если он остался незавершённым и длится >= min_duration
        if current_interval is not None and (current_interval['end_second'] - current_interval['start_second'] + 1) >= min_duration:
            matching_seconds.append({
                'start_second': current_interval['start_second'],
                'start_time': seconds_to_hms(current_interval['start_second']),
                'end_second': current_interval['end_second'],
                'end_time': seconds_to_hms(current_interval['end_second']),
                'duration_seconds': current_interval['end_second'] - current_interval['start_second'] + 1
            })

        print(f"Найдено {len(matching_seconds)} DS интервалов.")
        return matching_seconds

    except Exception as e:
        print(f"Ошибка при обнаружении DS интервалов: {e}")
        return []
