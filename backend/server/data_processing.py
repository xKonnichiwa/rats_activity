# data_processing.py

import numpy as np
import pyedflib
from scipy.signal import butter, lfilter, welch

def load_edf(file_path):
    """
    Загружает сигналы из EDF-файла.

    Параметры:
        file_path (str): Путь к EDF-файлу.

    Возвращает:
        signals (ndarray): Массив сигналов.
        signal_labels (list): Список меток каналов.
        header (dict): Заголовок EDF-файла.
        signal_headers (list): Список заголовков сигналов.
    """
    try:
        with pyedflib.EdfReader(file_path) as f:
            n = f.signals_in_file
            signal_labels = f.getSignalLabels()
            signals = np.zeros((n, f.getNSamples()[0]))
            for i in range(n):
                signals[i, :] = f.readSignal(i)
            header = f.getHeader()
            signal_headers = f.getSignalHeaders()
        print(f"Файл {file_path} успешно загружен.")
        return signals, signal_labels, header, signal_headers
    except Exception as e:
        print(f"Ошибка при загрузке файла {file_path}: {e}")
        return None, None, None, None

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    """
    Применяет полосовой фильтр к данным.

    Параметры:
        data (ndarray): Входные данные.
        lowcut (float): Нижняя граница частоты.
        highcut (float): Верхняя граница частоты.
        fs (float): Частота дискретизации.
        order (int): Порядок фильтра.

    Возвращает:
        y (ndarray): Отфильтрованные данные.
    """
    try:
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        y = lfilter(b, a, data)
        return y
    except Exception as e:
        print(f"Ошибка при фильтрации данных: {e}")
        return data

def extract_features(signals, fs):
    """
    Извлекает признаки из сигналов.

    Параметры:
        signals (ndarray): Массив сигналов.
        fs (float): Частота дискретизации.

    Возвращает:
        features (ndarray): Массив признаков.
        positions (ndarray): Массив позиций окон.
    """
    try:
        window_size = int(4 * fs)  # окна по 4 секунды
        step_size = int(2 * fs)    # шаг в 2 секунды
        features = []
        positions = []
        for start in range(0, signals.shape[1] - window_size, step_size):
            window = signals[:, start:start + window_size]
            # Временные признаки
            mean = np.mean(window, axis=1)
            std = np.std(window, axis=1)
            max_val = np.max(window, axis=1)
            min_val = np.min(window, axis=1)
            # Частотные признаки
            freqs, psd = welch(window, fs=fs, nperseg=window_size)
            delta_power = np.sum(psd[:, (freqs >= 0.5) & (freqs <= 4)], axis=1)
            theta_power = np.sum(psd[:, (freqs >= 4) & (freqs <= 8)], axis=1)
            total_power = np.sum(psd, axis=1)
            # Избежание деления на ноль
            total_power[total_power == 0] = 1
            delta_rel_power = delta_power / total_power
            theta_rel_power = theta_power / total_power
            feature_vector = np.hstack([mean, std, max_val, min_val, delta_rel_power, theta_rel_power])
            features.append(feature_vector)
            positions.append(start)
        features = np.array(features)
        positions = np.array(positions)
        return features, positions
    except Exception as e:
        print(f"Ошибка при извлечении признаков: {e}")
        return np.array([]), np.array([])
