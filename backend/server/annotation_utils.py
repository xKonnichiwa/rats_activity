# annotation_utils.py

import json
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

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
        logger.info(f"Аннотации из {json_file_path} успешно загружены.")
        return data
    except Exception as e:
        logger.error(f"Ошибка при загрузке JSON-файла {json_file_path}: {e}")
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
        logger.error(f"Ошибка при преобразовании времени '{time_str}': {e}")
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
        logger.error(f"Ошибка при преобразовании секунд '{seconds}': {e}")
        return "00:00:00"

def create_edf_annotations(grouped_intervals, matching_intervals):
    """
    Создаёт список аннотаций для EDF-файла.
    
    Параметры:
        grouped_intervals (list): Список интервалов SWD.
        matching_intervals (list): Список интервалов DS.
    
    Возвращает:
        annotations (list): Список аннотаций в формате (onset, duration, description).
    """
    annotations = []

    # Обработка grouped_intervals (маркеры swd1, swd2)
    for interval in grouped_intervals:
        start_sec = interval['start_second']
        end_sec = interval['end_second']

        # Добавление аннотаций начала и конца SWD
        annotations.append((start_sec, 0.0, 'swd1'))
        annotations.append((end_sec, 0.0, 'swd2'))

    # Обработка matching_intervals (маркеры ds1, ds2)
    for interval in matching_intervals:
        start_sec = interval['start_second']
        end_sec = interval['end_second']

        # Добавление аннотаций начала и конца DS
        annotations.append((start_sec, 0.0, 'ds1'))
        annotations.append((end_sec, 0.0, 'ds2'))

    logger.info(f"Всего новых аннотаций для добавления: {len(annotations)}")
    return annotations

def postprocess_predictions(predictions, positions, fs):
    """
    Постобработка предсказаний для генерации аннотаций.

    Параметры:
        predictions (ndarray): Предсказанные классы.
        positions (ndarray): Позиции окон.
        fs (float): Частота дискретизации.

    Возвращает:
        annotations (list): Список аннотаций в формате (onset, duration, description).
    """
    annotations = []
    window_duration = 4  # 4 секунды
    is_stack = []  # Для отслеживания соответствующих is1 и is2

    for i, pred in enumerate(predictions):
        if pred == 1:  # is1
            start_time = positions[i] / fs
            annotations.append((start_time, 0.0, 'is1'))
            is_stack.append(start_time)
            logger.debug(f"Добавлена аннотация is1: начало {start_time} секунд")
        elif pred == 2:  # is2
            if is_stack:
                end_time = (positions[i] + window_duration * fs) / fs
                annotations.append((end_time, 0.0, 'is2'))
                is_stack.pop()
                logger.debug(f"Добавлена аннотация is2: конец {end_time} секунд")
            else:
                logger.warning("Найдена аннотация 'is2' без соответствующей 'is1'. Пропуск.")
    if is_stack:
        logger.warning("Некоторые аннотации 'is1' не имеют соответствующей 'is2'.")
    return annotations


def convert_swd_annotations_to_tuples(swd_annotations):
    """
    Преобразует список SWD аннотаций из словарей в кортежи.

    Параметры:
        swd_annotations (list): Список SWD аннотаций в виде словарей.

    Возвращает:
        list: Список аннотаций в виде кортежей.
    """
    swd_tuples = []
    for interval in swd_annotations:
        try:
            # Добавляем начало SWD
            swd_tuples.append((interval['start_second'], 0.0, 'swd1'))
            # Добавляем конец SWD
            swd_tuples.append((interval['end_second'], 0.0, 'swd2'))
        except KeyError as e:
            logger.error(f"Ошибка при преобразовании SWD аннотации: отсутствует ключ {e} в интервале {interval}")
    return swd_tuples

def convert_ds_annotations_to_tuples(ds_annotations):
    """
    Преобразует список DS аннотаций из словарей в кортежи.

    Параметры:
        ds_annotations (list): Список DS аннотаций в виде словарей.

    Возвращает:
        list: Список аннотаций в виде кортежей.
    """
    ds_tuples = []
    for interval in ds_annotations:
        try:
            # Добавляем начало DS
            ds_tuples.append((interval['start_second'], 0.0, 'ds1'))
            # Добавляем конец DS
            ds_tuples.append((interval['end_second'], 0.0, 'ds2'))
        except KeyError as e:
            logger.error(f"Ошибка при преобразовании DS аннотации: отсутствует ключ {e} в интервале {interval}")
    return ds_tuples

def merge_overlapping_annotations(annotations, annotation_type):
    """
    Объединяет перекрывающиеся аннотации заданного типа.

    Параметры:
        annotations (list): Список кортежей (onset, duration, description).
        annotation_type (str): Тип аннотации ('is', 'swd', 'ds').

    Возвращает:
        list: Список объединённых аннотаций в формате (onset, duration, description).
    """
    # Извлекаем интервалы данного типа
    intervals = []
    stack = []
    for onset, duration, description in annotations:
        if description == f"{annotation_type}1":
            stack.append(onset)
        elif description == f"{annotation_type}2":
            if stack:
                start = stack.pop()
                end = onset
                intervals.append((start, end))
            else:
                logger.warning(f"Найдена аннотация {annotation_type}2 без соответствующей {annotation_type}1.")

    # Сортируем интервалы по времени начала
    intervals.sort(key=lambda x: x[0])

    # Объединяем перекрывающиеся интервалы
    merged = []
    for interval in intervals:
        if not merged:
            merged.append(interval)
        else:
            last = merged[-1]
            if interval[0] <= last[1]:  # Перекрытие
                merged[-1] = (last[0], max(last[1], interval[1]))
            else:
                merged.append(interval)

    # Преобразуем объединённые интервалы обратно в аннотации
    merged_annotations = []
    for start, end in merged:
        merged_annotations.append((start, 0.0, f"{annotation_type}1"))
        merged_annotations.append((end, 0.0, f"{annotation_type}2"))

    return merged_annotations

def process_annotations_to_pairs(annotations):
    """
    Преобразует список аннотаций в пары для каждого типа.
    Возвращает словарь с ключами 'is', 'swd', 'ds' и списками пар.
    """
    annotation_types = ['is', 'swd', 'ds']
    annotations_dict = {atype: [] for atype in annotation_types}

    for atype in annotation_types:
        pairs = []
        temp_pair = {}
        for ann in annotations:
            onset, duration, description = ann
            if description == f"{atype}1":
                temp_pair['start'] = onset
            elif description == f"{atype}2":
                temp_pair['end'] = onset
                if 'start' in temp_pair:
                    pairs.append(temp_pair)
                    temp_pair = {}
        annotations_dict[atype] = pairs
    return annotations_dict

def convert_annotations_from_json(annotations_json):
    """
    Преобразует аннотации из JSON-формата в список кортежей (onset, duration, description).
    """
    annotations = []
    for atype, pairs in annotations_json.items():
        for pair in pairs:
            annotations.append((pair['start'], 0.0, f"{atype}1"))
            annotations.append((pair['end'], 0.0, f"{atype}2"))
    return annotations

def validate_annotation_pairs(annotations, annotation_type):
    """
    Проверяет, что каждая аннотация {annotation_type}1 имеет соответствующую {annotation_type}2.

    Параметры:
        annotations (list): список кортежей (onset, duration, description).
        annotation_type (str): тип аннотации ('is', 'swd', 'ds').

    Возвращает:
        bool: True, если все пары корректны, иначе False.
    """
    stack = []
    for onset, duration, description in annotations:
        if description == f"{annotation_type}1":
            stack.append(onset)
        elif description == f"{annotation_type}2":
            if stack:
                stack.pop()
            else:
                logger.error(f"Найдена аннотация {annotation_type}2 без соответствующей {annotation_type}1.")
                return False
    if stack:
        logger.error(f"Некоторые аннотации {annotation_type}1 не имеют соответствующей {annotation_type}2.")
        return False
    return True

def save_signals_as_json(file_id: str, signals_data: dict, labels: list, output_dir: str = "data/json/"):
    """
    Сохраняет данные сигналов и метки каналов в JSON-файл.
    
    Параметры:
        file_id (str): Идентификатор файла.
        signals_data (dict): Данные сигналов.
        labels (list): Метки каналов.
        output_dir (str): Директория для сохранения JSON-файлов.
    
    Возвращает:
        str: Путь к сохранённому JSON-файлу или None в случае ошибки.
    """
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Создана директория для JSON-файлов: {output_dir}")
        except Exception as e:
            logger.error(f"Не удалось создать директорию {output_dir}: {e}")
            return None
    
    # Используйте правильный разделитель путей, чтобы избежать проблем в Windows
    json_filename = f"signals_{file_id}.json"
    json_path = os.path.join(output_dir, json_filename)
    
    data_to_save = {
        "signals": signals_data,
        "labels": labels
    }
    
    try:
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(data_to_save, json_file, ensure_ascii=False, indent=4)
        logger.info(f"Сигналы сохранены в: {json_path}")
        return json_path
    except Exception as e:
        logger.error(f"Ошибка при сохранении JSON-файла: {e}")
        return None
