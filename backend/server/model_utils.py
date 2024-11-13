# model_utils.py

import joblib
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
from tensorflow.keras.losses import Loss

class FocalLoss(Loss):
    def __init__(self, gamma=2., alpha=.25, **kwargs):
        """
        Инициализация FocalLoss.

        Параметры:
            gamma (float): Параметр фокусировки.
            alpha (float): Балансировка классов.
            **kwargs: Дополнительные аргументы.
        """
        super(FocalLoss, self).__init__(**kwargs)
        self.gamma = gamma
        self.alpha = alpha

    def call(self, y_true, y_pred):
        """
        Вычисление значения функции потерь.

        Параметры:
            y_true (tensor): Истинные метки.
            y_pred (tensor): Предсказанные вероятности.

        Возвращает:
            loss (tensor): Значение функции потерь.
        """
        y_true = K.cast(y_true, dtype='float32')
        epsilon = K.epsilon()
        y_pred = K.clip(y_pred, epsilon, 1. - epsilon)
        cross_entropy = -y_true * K.log(y_pred)
        weight = self.alpha * y_true * K.pow((1 - y_pred), self.gamma)
        focal_loss = weight * cross_entropy
        return K.mean(focal_loss)

def focal_loss_function(y_true, y_pred):
    """
    Функция потерь focal_loss, обёрнутая вокруг класса FocalLoss.
    """
    fl = FocalLoss()
    return fl(y_true, y_pred)

def load_model_keras(model_path):
    """
    Загружает модель Keras из файла с учётом кастомных объектов.

    Параметры:
        model_path (str): Путь к файлу модели.

    Возвращает:
        model (Model): Загруженная модель Keras или None при ошибке.
    """
    try:
        model = load_model(model_path, custom_objects={'FocalLoss': FocalLoss, 'focal_loss': focal_loss_function})
        print(f"Модель успешно загружена из файла: {model_path}")
        return model
    except Exception as e:
        print(f"Ошибка при загрузке модели из {model_path}: {e}")
        return None

def predict(model, X):
    """
    Делает предсказание на основе входных данных X.

    Параметры:
        model (Model): Модель для предсказания.
        X (ndarray): Входные данные.

    Возвращает:
        y_pred (ndarray): Предсказанные вероятности.
    """
    try:
        y_pred = model.predict(X)
        return y_pred
    except Exception as e:
        print(f"Ошибка при предсказании: {e}")
        return None
