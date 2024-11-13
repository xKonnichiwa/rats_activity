# edf_utils.py

import os
import shutil
import logging
from fastapi import UploadFile
import pyedflib
import numpy as np

logger = logging.getLogger(__name__)

def save_uploaded_file(file: UploadFile, upload_dir: str):
    """
    Сохраняет загруженный файл в указанную директорию.

    Параметры:
        file (UploadFile): Загруженный файл.
        upload_dir (str): Путь к директории для сохранения файла.

    Возвращает:
        str: Путь к сохранённому файлу или None в случае ошибки.
    """
    try:
        file_location = os.path.join(upload_dir, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Файл сохранён в: {file_location}")
        return file_location
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла {file.filename}: {e}")
        return None

def read_edf_with_annotations(file_path):
    """
    Читает EDF-файл и извлекает сигналы и аннотации.

    Параметры:
        file_path (str): Путь к EDF-файлу.

    Возвращает:
        signals (ndarray): Массив сигналов.
        signal_labels (list): Метки сигналов.
        header (dict): Заголовок EDF-файла.
        signal_headers (list): Заголовки сигналов.
        existing_annotations (list): Список существующих аннотаций.
    """
    try:
        f = pyedflib.EdfReader(file_path)
        num_signals = f.signals_in_file
        signal_labels = f.getSignalLabels()
        signals = np.zeros((num_signals, f.getNSamples()[0]))
        for i in range(num_signals):
            signals[i, :] = f.readSignal(i)
        header = f.getHeader()
        signal_headers = f.getSignalHeaders()
        existing_annotations = []
        annotations = f.readAnnotations()
        for onset, duration, description in zip(annotations[0], annotations[1], annotations[2]):
            existing_annotations.append((onset, duration, description))
        f.close()
        logger.info(f"EDF-файл {file_path} успешно загружен с аннотациями.")
        return signals, signal_labels, header, signal_headers, existing_annotations
    except Exception as e:
        logger.error(f"Ошибка при загрузке EDF-файла {file_path}: {e}")
        return None, None, None, None, None

def write_edf_with_annotations(original_file_path, annotations, output_file_path, header, signal_headers, signals):
    """
    Записывает EDF-файл с добавленными аннотациями.

    Параметры:
        original_file_path (str): Путь к оригинальному EDF-файлу.
        annotations (list): Список аннотаций в формате (onset, duration, description).
        output_file_path (str): Путь для сохранения нового EDF-файла.
        header (dict): Заголовок оригинального EDF-файла.
        signal_headers (list): Заголовки сигналов.
        signals (ndarray): Массив сигналов.

    Возвращает:
        bool: True при успешной записи, False иначе.
    """
    try:
        num_channels = len(signals)
        logger.debug(f"Инициализация EdfWriter для файла {output_file_path} с {num_channels} каналами.")
        with pyedflib.EdfWriter(output_file_path, n_channels=num_channels, file_type=pyedflib.FILETYPE_EDFPLUS) as writer:
            logger.debug("Установка заголовка EDF.")
            writer.setHeader(header)
            for i in range(num_channels):
                logger.debug(f"Установка заголовка сигнала для канала {i}.")
                writer.setSignalHeader(i, signal_headers[i])
            logger.debug("Запись сигналов.")
            writer.writeSamples(signals)

            logger.debug("Добавление аннотаций.")
            for onset, duration, description in annotations:
                logger.debug(f"Добавление аннотации: onset={onset}, duration={duration}, description={description}")
                writer.writeAnnotation(onset, duration, description)

        logger.info(f"EDF-файл с аннотациями успешно сохранён: {output_file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при записи EDF-файла {output_file_path}: {e}")
        return False
