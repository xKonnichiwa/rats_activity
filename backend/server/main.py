# main.py

import os
import uuid
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from edf_utils import (
    save_uploaded_file,
    read_edf_with_annotations,
    write_edf_with_annotations
)


from annotation_utils import save_signals_as_json
from data_processing import bandpass_filter, extract_features, load_edf
from model_utils import load_model_keras
from swd_detection import detect_swd
from ds_detection import detect_ds
from annotation_utils import (
    postprocess_predictions,
    convert_swd_annotations_to_tuples,
    convert_ds_annotations_to_tuples,
    merge_overlapping_annotations,
    process_annotations_to_pairs,
    convert_annotations_from_json,
    validate_annotation_pairs
)

import logging

app = FastAPI()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Разрешаем CORS для взаимодействия с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В реальном проекте замените на список допустимых источников
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Определение директорий для загрузок и сохранения JSON-файлов
UPLOAD_DIR = "data/uploads"
JSON_DIR = "data/json"

# Создание директорий, если они не существуют
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

# Загружаем модель при запуске приложения
model = load_model_keras('cnn_classifier.h5')
if model is None:
    logger.error("Не удалось загрузить модель 'cnn_classifier.h5'")
    raise Exception("Не удалось загрузить модель")

# Хранилище для файлов и данных
files_data = {}

@app.post("/upload-edf/")
async def upload_edf(file: UploadFile = File(...)):
    # Генерация уникального file_id
    unique_id = str(uuid.uuid4())
    file_id = f"{unique_id}_{file.filename}"
    
    # Сохранение файла
    file_location = save_uploaded_file(file, UPLOAD_DIR)
    if not file_location:
        logger.error(f"Не удалось сохранить файл: {file.filename}")
        raise HTTPException(status_code=500, detail="Не удалось сохранить файл")
    
    # Инициализация записи в files_data
    files_data[file_id] = {'file_path': file_location}
    logger.info(f"Файл '{file_id}' загружен и сохранён по пути: {file_location}")
    
    # Загрузка и обработка EDF-файла
    signals, signal_labels, header, signal_headers, existing_annotations = read_edf_with_annotations(file_location)
    if signals is None:
        logger.error(f"Не удалось загрузить EDF-файл: {file_location}")
        raise HTTPException(status_code=500, detail="Не удалось загрузить EDF-файл")
    
    logger.info(f"Сигналы загружены для файла '{file_id}'. Каналов: {len(signal_labels)}")
    
    # Применение фильтра к каждому каналу
    fs = 400  # Частота дискретизации
    lowcut = 0.5
    highcut = 100
    filtered_signals = []
    for i in range(signals.shape[0]):
        filtered_signal = bandpass_filter(signals[i], lowcut, highcut, fs)
        filtered_signals.append(filtered_signal)
    filtered_signals = np.array(filtered_signals)
    
    logger.info(f"Применён фильтр к сигналам файла '{file_id}'")
    
    # Извлечение признаков
    features, positions = extract_features(filtered_signals, fs)
    if features.size == 0:
        logger.error(f"Не удалось извлечь признаки из данных файла '{file_id}'")
        raise HTTPException(status_code=500, detail="Не удалось извлечь признаки из данных")
    
    logger.info(f"Признаки извлечены для файла '{file_id}'")
    
    # Подготовка данных для модели
    X = features.reshape((features.shape[0], features.shape[1], 1))
    
    # Предсказание
    try:
        y_pred_probs = model.predict(X)
        y_pred_classes = np.argmax(y_pred_probs, axis=1)
        logger.info(f"Предсказания модели выполнены для файла '{file_id}'")
    except Exception as e:
        logger.error(f"Ошибка при предсказании модели для файла '{file_id}': {e}")
        raise HTTPException(status_code=500, detail="Ошибка при предсказании модели")
    
    # Постобработка предсказаний для генерации аннотаций
    annotations_pred = postprocess_predictions(y_pred_classes, positions, fs)
    
    logger.info(f"Постобработка предсказаний завершена для файла '{file_id}'")
    
    # Объединение аннотаций IS
    if existing_annotations:
        all_is_annotations = list(existing_annotations) + annotations_pred
    else:
        all_is_annotations = annotations_pred
    
    logger.info(f"Аннотации IS объединены для файла '{file_id}'")
    
    # Сохранение временного EDF-файла с IS аннотациями
    temp_edf_path = os.path.join(UPLOAD_DIR, f"temp_{file_id}.edf")
    success = write_edf_with_annotations(
        original_file_path=file_location,
        annotations=all_is_annotations,
        output_file_path=temp_edf_path,
        header=header,
        signal_headers=signal_headers,
        signals=signals
    )
    if not success:
        logger.error(f"Не удалось сохранить временный EDF-файл с аннотациями IS: {temp_edf_path}")
        raise HTTPException(status_code=500, detail="Не удалось сохранить временный EDF-файл с аннотациями IS")
    
    logger.info(f"Временный EDF-файл с аннотациями IS сохранён: {temp_edf_path}")
    
    # Обнаружение SWD на аннотированном EDF-файле с IS аннотациями
    try:
        swd_annotations = detect_swd(temp_edf_path)
        swd_annotation_tuples = convert_swd_annotations_to_tuples(swd_annotations)
        logger.info(f"SWD аннотации обнаружены для файла '{file_id}'")
    except Exception as e:
        logger.error(f"Ошибка при обнаружении SWD аннотаций для файла '{file_id}': {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обнаружении SWD аннотаций")
    
    # Обнаружение DS на аннотированном EDF-файле с IS аннотациями
    try:
        ds_annotations = detect_ds(temp_edf_path)
        ds_annotation_tuples = convert_ds_annotations_to_tuples(ds_annotations)
        logger.info(f"DS аннотации обнаружены для файла '{file_id}'")
    except Exception as e:
        logger.error(f"Ошибка при обнаружении DS аннотаций для файла '{file_id}': {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обнаружении DS аннотаций")
    
    # Объединение всех аннотаций
    final_annotations = all_is_annotations + swd_annotation_tuples + ds_annotation_tuples
    
    logger.info(f"Все аннотации объединены для файла '{file_id}'")
    
    # Объединение перекрывающихся аннотаций по типам
    merged_is_annotations = merge_overlapping_annotations(final_annotations, 'is')
    merged_swd_annotations = merge_overlapping_annotations(final_annotations, 'swd')
    merged_ds_annotations = merge_overlapping_annotations(final_annotations, 'ds')
    
    logger.info(f"Перекрывающиеся аннотации объединены для файла '{file_id}'")
    
    # Проверка корректности пар аннотаций
    if not validate_annotation_pairs(merged_is_annotations, 'is'):
        logger.warning(f"Ошибка в парах аннотаций IS для файла '{file_id}'")
    if not validate_annotation_pairs(merged_swd_annotations, 'swd'):
        logger.warning(f"Ошибка в парах аннотаций SWD для файла '{file_id}'")
    if not validate_annotation_pairs(merged_ds_annotations, 'ds'):
        logger.warning(f"Ошибка в парах аннотаций DS для файла '{file_id}'")
    
    # Собираем все объединённые аннотации
    final_merged_annotations = merged_is_annotations + merged_swd_annotations + merged_ds_annotations
    final_merged_annotations.sort(key=lambda x: x[0])
    
    # Запись конечного EDF-файла с всеми аннотациями
    final_edf_path = os.path.join(UPLOAD_DIR, f"final_{file_id}.edf")
    success = write_edf_with_annotations(
        original_file_path=file_location,
        annotations=final_merged_annotations,
        output_file_path=final_edf_path,
        header=header,
        signal_headers=signal_headers,
        signals=signals
    )
    if not success:
        logger.error(f"Не удалось сохранить конечный EDF-файл с аннотациями: {final_edf_path}")
        raise HTTPException(status_code=500, detail="Не удалось сохранить конечный EDF-файл с аннотациями")
    
    logger.info(f"Конечный EDF-файл с аннотациями сохранён: {final_edf_path}")
    
    # Добавление финального файла в files_data
    final_file_id = f"final_{file_id}"
    files_data[final_file_id] = {
        'file_path': final_edf_path,
        'signals': signals,
        'signal_labels': signal_labels,
        'annotations': final_merged_annotations,
        'header': header,
        'signal_headers': signal_headers
    }
    logger.info(f"Файл '{final_file_id}' добавлен в хранилище files_data")
    
    # Сохранение обработанных данных
    files_data[file_id]['signals'] = signals
    files_data[file_id]['signal_labels'] = signal_labels
    files_data[file_id]['annotations'] = final_merged_annotations
    files_data[file_id]['header'] = header
    files_data[file_id]['signal_headers'] = signal_headers
    files_data[file_id]['final_edf_path'] = final_edf_path
    
    logger.info(f"Обработанные данные сохранены для файла '{file_id}'")
    
    return {"file_id": file_id, "final_file_id": final_file_id}


@app.get("/get-signals/{file_id}")
async def get_signals(file_id: str):
    file_info = files_data.get(file_id)
    if not file_info or 'signals' not in file_info:
        logger.warning(f"Файл не найден для file_id: {file_id}")
        raise HTTPException(status_code=404, detail="Файл не найден или сигналы не обработаны")

    signals = file_info['signals']
    labels = file_info.get('signal_labels', [])

    # Преобразование сигналов в список для JSON
    signals_data = {str(i): signals[i][:30*60*400].tolist() for i in range(signals.shape[0])}

    # Сохранение данных в JSON-файл
    json_path = save_signals_as_json(file_id, signals_data, labels, output_dir=JSON_DIR)
    if json_path:
        logger.info(f"JSON-файл сохранён: {json_path}")
    else:
        logger.error("Не удалось сохранить JSON-файл")
        raise HTTPException(status_code=500, detail="Не удалось сохранить JSON-файл")
    
    # Возврат данных клиенту
    return {'signals': signals_data, 'labels': labels}

@app.get("/get-annotations/{file_id}")
async def get_annotations(file_id: str):
    file_info = files_data.get(file_id)
    if not file_info or 'annotations' not in file_info:
        logger.warning(f"Файл не найден или аннотации не обработаны для file_id: {file_id}")
        raise HTTPException(status_code=404, detail="Файл не найден или аннотации не обработаны")
    annotations = file_info['annotations']
    # Преобразуем аннотации в пары
    annotations_dict = process_annotations_to_pairs(annotations)
    return annotations_dict

@app.post("/update-annotations/{file_id}")
async def update_annotations(file_id: str, new_annotations: dict):
    file_info = files_data.get(file_id)
    if not file_info:
        logger.warning(f"Файл не найден для обновления аннотаций: {file_id}")
        raise HTTPException(status_code=404, detail="Файл не найден")
    original_file_path = file_info['file_path']
    output_file_path = os.path.join(UPLOAD_DIR, f"updated_{file_id}")

    # Преобразование новых аннотаций из JSON в список кортежей
    updated_annotations = convert_annotations_from_json(new_annotations)

    # Сохранение EDF-файла с новыми аннотациями
    success = write_edf_with_annotations(
        original_file_path,
        updated_annotations,
        output_file_path,
        file_info['header'],
        file_info['signal_headers'],
        file_info['signals']
    )
    if not success:
        logger.error(f"Не удалось обновить EDF-файл: {output_file_path}")
        raise HTTPException(status_code=500, detail="Не удалось обновить EDF-файл")
    # Обновляем информацию о файле
    files_data[file_id]['updated_file_path'] = output_file_path
    logger.info(f"EDF-файл обновлён: {output_file_path}")
    return {"message": "EDF-файл успешно обновлён"}

@app.get("/download-edf/{file_id}")
async def download_edf(file_id: str):
    file_info = files_data.get(file_id)
    if file_info:
        updated_file_path = file_info.get('updated_file_path')
        if updated_file_path:
            return FileResponse(
                path=updated_file_path,
                filename=f"updated_{file_id}",
                media_type='application/octet-stream'
            )
        else:
            return FileResponse(
                path=file_info,
                filename=file_id,
                media_type='application/octet-stream'
            )
    else:
        logger.warning(f"file_id {file_id} не найден в files_data")
        raise HTTPException(status_code=404, detail="Обновлённый файл не найден")
    

