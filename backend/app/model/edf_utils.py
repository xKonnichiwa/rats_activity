# edf_utils.py

import numpy as np
import pyedflib

def load_edf_with_annotations(file_path):
    """
    Загружает EDF-файл вместе с существующими аннотациями.

    Параметры:
        file_path (str): Путь к EDF-файлу.

    Возвращает:
        signals (ndarray): Массив сигналов.
        signal_labels (list): Список меток каналов.
        header (dict): Заголовок EDF-файла.
        signal_headers (list): Список заголовков сигналов.
        existing_annotations (list): Список существующих аннотаций.
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
            # Чтение существующих аннотаций
            existing_annotations = []
            annotations = f.readAnnotations()
            for onset, duration, description in zip(annotations[0], annotations[1], annotations[2]):
                existing_annotations.append((onset, duration, description))
        print(f"Файл {file_path} успешно загружен с аннотациями.")
        return signals, signal_labels, header, signal_headers, existing_annotations
    except Exception as e:
        print(f"Ошибка при загрузке файла {file_path}: {e}")
        return None, None, None, None, None

def save_annotated_edf(original_file_path, annotated_file_path, new_annotations, header, signal_headers, signals, existing_annotations):
    """
    Сохраняет EDF-файл с объединёнными аннотациями.

    Параметры:
        original_file_path (str): Путь к исходному EDF-файлу.
        annotated_file_path (str): Путь для сохранения аннотированного EDF-файла.
        new_annotations (list): Список новых аннотаций для добавления.
        header (dict): Заголовок EDF-файла.
        signal_headers (list): Список заголовков сигналов.
        signals (ndarray): Массив сигналов.
        existing_annotations (list): Список существующих аннотаций.
    """
    try:
        # Объединяем существующие и новые аннотации
        all_annotations = existing_annotations + new_annotations
        # Сортируем аннотации по времени начала
        all_annotations.sort(key=lambda x: x[0])

        with pyedflib.EdfWriter(annotated_file_path, n_channels=len(signals), file_type=pyedflib.FILETYPE_EDFPLUS) as writer:
            writer.setHeader(header)
            for i in range(len(signals)):
                writer.setSignalHeader(i, signal_headers[i])
            writer.writeSamples(signals)

            # Добавляем все аннотации
            for onset, duration, description in all_annotations:
                writer.writeAnnotation(onset, duration, description)

        print(f"Аннотированный EDF-файл сохранён: {annotated_file_path}")
    except Exception as e:
        print(f"Ошибка при сохранении аннотированного EDF-файла: {e}")
