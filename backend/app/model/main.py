# main.py

import os
import numpy as np
from .model_utils import load_model_keras
from .data_processing import load_edf, bandpass_filter, extract_features
from .edf_utils import save_annotated_edf, load_edf_with_annotations
from .annotation_utils import load_json_annotations, create_edf_annotations, seconds_to_hms
from .swd_detection import detect_swd
from .ds_detection import detect_ds

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
    for i, pred in enumerate(predictions):
        if pred == 1:  # is1
            start_time = positions[i] / fs
            annotations.append((start_time, 0.0, 'is1'))
        elif pred == 2:  # is2
            end_time = (positions[i] + window_duration * fs) / fs
            annotations.append((end_time, 0.0, 'is2'))
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
            print(f"Ошибка при преобразовании SWD аннотации: отсутствует ключ {e} в интервале {interval}")
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
            print(f"Ошибка при преобразовании DS аннотации: отсутствует ключ {e} в интервале {interval}")
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
                print(f"Найдена аннотация {annotation_type}2 без соответствующей {annotation_type}1.")

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

def annotate_edf(unannotated_edf_path):
    """
    Аннотирует EDF-файл, используя модель и выполняя детекцию IS, SWD и DS.

    Параметры:
        unannotated_edf_path (str): Путь к неаннотированному EDF-файлу.

    Возвращает:
        str: "success" в случае успешного выполнения, иначе сообщение об ошибке.
    """
    try:
        fs = 400  # Частота дискретизации
        lowcut = 0.5
        highcut = 100

        # Пути к файлам
        model_path = r"model\cnn_classifier.h5"
        annotated_is_edf_path = r"annotated_is_file.edf"
        file_name, file_extension = os.path.splitext(unannotated_edf_path)
        final_annotated_edf_path = f"{file_name}_annotated{file_extension}"

        # Загрузка модели
        model = load_model_keras(model_path)
        if model is None:
            return "Ошибка: не удалось загрузить модель."

        # Загрузка EDF-файла с существующими аннотациями
        signals, signal_labels, header, signal_headers, existing_annotations = load_edf_with_annotations(unannotated_edf_path)
        if signals is None:
            return "Ошибка: не удалось загрузить EDF-файл."

        # Применение фильтра к каждому каналу
        filtered_signals = []
        for i in range(signals.shape[0]):
            filtered_signal = bandpass_filter(signals[i], lowcut, highcut, fs)
            filtered_signals.append(filtered_signal)
        filtered_signals = np.array(filtered_signals)

        # Извлечение признаков
        features, positions = extract_features(filtered_signals, fs)
        if features.size == 0:
            return "Ошибка: не удалось извлечь признаки из данных."

        # Подготовка данных для модели
        X = features.reshape((features.shape[0], features.shape[1], 1))

        # Предсказание
        y_pred_probs = model.predict(X)
        y_pred_classes = np.argmax(y_pred_probs, axis=1)

        # Постобработка предсказаний
        annotations_pred = postprocess_predictions(y_pred_classes, positions, fs)

        # Объединение аннотаций IS
        all_is_annotations = existing_annotations + annotations_pred if existing_annotations else annotations_pred

        # Сохранение временного EDF-файла с IS аннотациями
        save_annotated_edf(
            unannotated_edf_path,
            annotated_is_edf_path,
            annotations_pred,
            header,
            signal_headers,
            signals,
            existing_annotations if existing_annotations else []
        )

        # Обнаружение SWD и DS
        swd_annotations = detect_swd(annotated_is_edf_path)
        swd_annotation_tuples = convert_swd_annotations_to_tuples(swd_annotations)

        ds_annotations = detect_ds(annotated_is_edf_path)
        ds_annotation_tuples = convert_ds_annotations_to_tuples(ds_annotations)

        # Объединение всех аннотаций
        final_annotations = all_is_annotations + swd_annotation_tuples + ds_annotation_tuples

        # Объединение перекрывающихся аннотаций по типам
        merged_is_annotations = merge_overlapping_annotations(final_annotations, 'is')
        merged_swd_annotations = merge_overlapping_annotations(final_annotations, 'swd')
        merged_ds_annotations = merge_overlapping_annotations(final_annotations, 'ds')

        # Собираем все объединённые аннотации
        final_merged_annotations = merged_is_annotations + merged_swd_annotations + merged_ds_annotations

        # Сортировка всех аннотаций по времени начала
        final_merged_annotations.sort(key=lambda x: x[0])

        # Сохранение окончательного EDF-файла с IS, SWD и DS аннотациями
        save_annotated_edf(
            unannotated_edf_path,
            final_annotated_edf_path,
            final_merged_annotations,
            header,
            signal_headers,
            signals,
            existing_annotations if existing_annotations else []
        )

        return "success"

    except Exception as e:
        return f"Ошибка: {str(e)}"
