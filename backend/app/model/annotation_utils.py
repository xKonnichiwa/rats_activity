# annotation_utils.py

import json

def load_json_annotations(json_file_path):
    """
    Загружает аннотации из JSON-файла.
    
    Параметры:
        json_file_path (str): Путь к JSON-файлу.
    
    Возвращает:
        data (list): Список аннотаций.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print(f"Аннотации из {json_file_path} успешно загружены.")
        return data
    except Exception as e:
        print(f"Ошибка при загрузке JSON-файла {json_file_path}: {e}")
        return []

def time_str_to_seconds(time_str):
    """
    Преобразует строку времени в секунды.
    
    Параметры:
        time_str (str): Время в формате 'чч:мм:сс'.
    
    Возвращает:
        seconds (float): Время в секундах.
    """
    try:
        parts = time_str.strip().split(':')
        parts = [float(p) for p in parts]
        if len(parts) == 3:
            h, m, s = parts
        elif len(parts) == 2:
            h, m = parts
            s = 0
        elif len(parts) == 1:
            h = parts[0]
            m = s = 0
        else:
            h = m = s = 0
        return h * 3600 + m * 60 + s
    except Exception as e:
        print(f"Ошибка при преобразовании времени '{time_str}': {e}")
        return 0

def seconds_to_hms(seconds):
    """
    Преобразует секунды в строку формата 'чч:мм:сс'.
    
    Параметры:
        seconds (float): Время в секундах.
    
    Возвращает:
        hms_str (str): Время в формате 'чч:мм:сс'.
    """
    try:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:.0f}"
    except Exception as e:
        print(f"Ошибка при преобразовании секунд '{seconds}': {e}")
        return "00:00:00"

def create_edf_annotations(grouped_intervals, matching_intervals):
    """
    Создаёт список аннотаций для EDF-файла.
    
    Параметры:
        grouped_intervals (list): Список интервалов SWD из grouped_intervals.json.
        matching_intervals (list): Список интервалов DS из matching_intervals.json.
    
    Возвращает:
        annotations (list): Список аннотаций в формате (onset, duration, description).
    """
    annotations = []

    # Обработка grouped_intervals.json (маркеры swd1, swd2)
    for interval in grouped_intervals:
        start_sec = time_str_to_seconds(interval['start_time'])
        end_sec = time_str_to_seconds(interval['end_time'])

        # Добавление аннотаций начала и конца SWD
        annotations.append((start_sec, 0.0, 'swd1'))
        annotations.append((end_sec, 0.0, 'swd2'))

    # Обработка matching_intervals.json (маркеры ds1, ds2)
    for interval in matching_intervals:
        start_sec = time_str_to_seconds(interval['start_time'])
        end_sec = time_str_to_seconds(interval['end_time'])

        # Добавление аннотаций начала и конца DS
        annotations.append((start_sec, 0.0, 'ds1'))
        annotations.append((end_sec, 0.0, 'ds2'))

    print(f"Всего новых аннотаций для добавления: {len(annotations)}")
    return annotations

# Добавляем алиас для совместимости
time_to_seconds = time_str_to_seconds
