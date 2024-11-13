import os
import mne
import numpy as np
import matplotlib.pyplot as plt
import shutil
from model.main import annotate_edf
from model.annotation_utils import seconds_to_hms
from matplotlib.widgets import Slider
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QMainWindow, QPushButton,
    QLabel, QVBoxLayout, QWidget, QMessageBox, QSplitter, QListWidget, QHBoxLayout, QInputDialog, QLineEdit
)

def process_edf(file_path):
    return mne.io.read_raw_edf(file_path, preload=False)

class MainWindow(QMainWindow):
    file_path = "" # Пуль к файлу
    step_size = 1   
    def __init__(self):
        """
        Инициализация окна, отрисовка основных эл-тов интерфейса
        """
        super().__init__()
        self.setWindowTitle("Классификация ЭКоГ по EDF") # Имя окна
        self.setWindowIcon(QIcon("rat.ico")) # Иконка для окна
        self.setMinimumSize(1024, 768) # Минимальный размер
        self.showMaximized() # Разворачиет окно на весь экран (в окне)

        self.raw = None # Наполнитель для данных с EDF
        self.predictions = None # Наполнитель для предсказания

        # Верхний лейбл (информационный)
        self.label_info = QLabel('Файл формата .edf не загружен', self)
        self.label_info.setAlignment(Qt.AlignCenter)
        self.label_info.setFixedHeight(20)

        # Панель контроля
        self.button_load = QPushButton('Загрузить EDF-файл', self)
        self.button_load.clicked.connect(self.load_file)

        self.button_predict = QPushButton('Кластеризовать диаграммы', self)
        self.button_predict.clicked.connect(self.save_file)
        self.button_predict.setEnabled(False)

        self.button_save = QPushButton('Сохранить аннотацию', self)
        self.button_save.clicked.connect(self.save_file)
        self.button_save.setEnabled(False)

        self.button_zoom_in_height = QPushButton('⬆️', self)
        self.button_zoom_in_height.setFixedWidth(25)
        self.button_zoom_out_height = QPushButton('⬇️', self)
        self.button_zoom_out_height.setFixedWidth(25)
        self.button_zoom_in_width = QPushButton('➡️', self)
        self.button_zoom_in_width.setFixedWidth(25)
        self.button_zoom_out_width = QPushButton('⬅️', self)
        self.button_zoom_out_width.setFixedWidth(25)
        self.button_zoom_in = QPushButton('🔍+', self)
        self.button_zoom_in.setFixedWidth(25)
        self.button_zoom_out = QPushButton('🔍-', self)
        self.button_zoom_out.setFixedWidth(25)

        self.button_zoom_in_height.clicked.connect(self.zoom_in_height)
        self.button_zoom_out_height.clicked.connect(self.zoom_out_height)
        self.button_zoom_in_width.clicked.connect(self.zoom_in_width)
        self.button_zoom_out_width.clicked.connect(self.zoom_out_width)
        self.button_zoom_in.clicked.connect(self.zoom_in)
        self.button_zoom_out.clicked.connect(self.zoom_out)

        self.annotation_label = QLabel("Аннотация:", self)
        self.annotation_label.setAlignment(Qt.AlignCenter)
        self.annotation_list = QListWidget()
        self.annotation_list.itemClicked.connect(self.jump_to_annotation)

        control_layout = QVBoxLayout()
        control_layout.addWidget(self.button_load)
        control_layout.addWidget(self.button_save)
        control_layout.addWidget(self.annotation_label)
        control_layout.addWidget(self.annotation_list)

        self.button_edit_annotation = QPushButton('Редактировать аннотацию', self)
        self.button_edit_annotation.clicked.connect(self.edit_annotation)
        self.button_edit_annotation.setEnabled(False)
        control_layout.addWidget(self.button_edit_annotation)

        # Добавление кнопки для добавления аннотаций
        self.button_add_annotation = QPushButton('Добавить 2 аннотации', self)
        self.button_add_annotation.clicked.connect(self.add_annotations)
        self.button_add_annotation.setEnabled(False)
        control_layout.addWidget(self.button_add_annotation)

        self.button_toggle_theme = QPushButton('Сменить тему', self)
        self.button_toggle_theme.clicked.connect(self.toggle_theme)
        control_layout.addWidget(self.button_toggle_theme)


        # Добавление кнопки для удаления аннотаций
        self.button_delete_annotation = QPushButton('Удалить аннотацию', self)
        self.button_delete_annotation.clicked.connect(self.delete_annotation)
        self.button_delete_annotation.setEnabled(False)
        control_layout.addWidget(self.button_delete_annotation)

        # Активируем кнопку при выборе аннотации
        self.annotation_list.itemSelectionChanged.connect(
            lambda: self.button_delete_annotation.setEnabled(bool(self.annotation_list.selectedItems()))
        )



        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(self.button_zoom_in_height)
        zoom_layout.addWidget(self.button_zoom_out_height)
        zoom_layout.addWidget(self.button_zoom_in_width)
        zoom_layout.addWidget(self.button_zoom_out_width)
        zoom_layout.addWidget(self.button_zoom_in)
        zoom_layout.addWidget(self.button_zoom_out)

        control_layout.addLayout(zoom_layout)

        control_panel = QWidget()
        control_panel.setLayout(control_layout)

        # График
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.ax.axis('off') # Убираем отображение осей для большого графика
        self.canvas = FigureCanvas(self.figure) # КАНВАС

        # Разделение на три оси
        self.ax1 = self.figure.add_subplot(3, 1, 1, position=[0.05, 0.7, 0.9, 0.25])
        self.ax2 = self.figure.add_subplot(3, 1, 2, position=[0.05, 0.4, 0.9, 0.25])
        self.ax3 = self.figure.add_subplot(3, 1, 3, position=[0.05, 0.1, 0.9, 0.25])

        # Включаем отображение для осей
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.axis('on')

        # Установка цвета для каждого канала
        self.channel_colors = ['red', 'green', 'blue']

        # Слайдер
        self.slider_ax = self.figure.add_axes([0.1, 0.02, 0.8, 0.04], facecolor='lightgoldenrodyellow')
        # Изначально макс. размер указывается на 0, после загрузки файла,
        # в зависимости от файлаУстанавливается размер слайдера
        self.slider = Slider(self.slider_ax, 'Время, сек.', 0, 0, valinit=0, valstep=1)
        self.slider.on_changed(self.update_plot)

        # Разделитель
        splitter = QSplitter()
        splitter.addWidget(control_panel)
        splitter.addWidget(self.canvas)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 5)

        # Основной бокс
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.label_info)
        main_layout.addWidget(splitter)

        # Контейнер
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def zoom_in_height(self):
        self.adjust_axes(scale_x=1.0, scale_y=1.2)

    def zoom_out_height(self):
        self.adjust_axes(scale_x=1.0, scale_y=0.8)

    def zoom_in_width(self):
        self.adjust_axes(scale_x=1.2, scale_y=1.0)

    def zoom_out_width(self):
        self.adjust_axes(scale_x=0.8, scale_y=1.0)

    def zoom_in(self):
        self.adjust_axes(scale_x=1.2, scale_y=1.2)

    def zoom_out(self):
        self.adjust_axes(scale_x=0.8, scale_y=0.8)

    def adjust_axes(self, scale_x=1.0, scale_y=1.0):
        """
        Масштабирует оси графиков по указанным коэффициентам.
        scale_x : float
            Коэффициент масштабирования по оси X.
        scale_y : float
            Коэффициент масштабирования по оси Y.
        """
        for ax in [self.ax1, self.ax2, self.ax3]:
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            # Вычисление новых пределов
            new_xlim = [(xlim[0] + (xlim[1] - xlim[0]) * (1 - scale_x) / 2),
                        (xlim[1] - (xlim[1] - xlim[0]) * (1 - scale_x) / 2)]
            new_ylim = [(ylim[0] + (ylim[1] - ylim[0]) * (1 - scale_y) / 2),
                        (ylim[1] - (ylim[1] - ylim[0]) * (1 - scale_y) / 2)]

            ax.set_xlim(new_xlim)
            ax.set_ylim(new_ylim)

        # Обновление графика
        self.canvas.draw()

    def load_file(self):
        """
        Функция загружает файл для дальнейшего анализа.\n
        Вызывается после нажатия пользователя на кнопку\n

        По умолчанию задан корневой путь - ""
        """
        file_name, file_extension = os.path.splitext(self.file_path)
        self.file_path, _ = QFileDialog.getOpenFileName(self, "Загрузить EDF-файл", "", "EDF-файлы (*.edf)")
        if self.file_path:
            # Обновление лейбла с информацией о загружаемом файле
            self.label_info.setText(f"Загрузка файла: {os.path.basename(self.file_path)}...")

            # Вызываем функцию annotate_edf
            status = annotate_edf(self.file_path)

            # Проверяем статус выполнения
            if status == "success":
                try:
                    file_name, file_extension = os.path.splitext(self.file_path)
                    self.raw = process_edf(f"{file_name}_annotated{file_extension}")
                    self.label_info.setText(f"Загруженный файл: {os.path.basename(self.file_path)}")

                    total_duration = self.raw.times[-1]
                    max_time = max(0, total_duration - 10)

                    self.slider.valmin = 0
                    self.slider.valmax = max_time
                    self.slider.set_val(0)
                    self.slider.ax.set_xlim(0, max_time)

                    self.init_plot()
                    self.update_annotation_list()

                    self.button_save.setEnabled(True)
                    self.button_add_annotation.setEnabled(True)
                except Exception as e:
                    self.label_info.setText(f"Ошибка при загрузке файла: {os.path.basename(self.file_path)} - {e}")
            else:
                self.label_info.setText(f"Не удалось аннотировать файл: {os.path.basename(self.file_path)}.")
        else:
            self.label_info.setText("Файл не выбран.")

    def edit_annotation(self):
        """
        Редактирование выбранной аннотации в списке (включая текст и время).
        """
        selected_item = self.annotation_list.currentItem()
        if selected_item:
            # Получаем текущий текст и время аннотации
            current_text = selected_item.text().split(" - ")[0]
            current_time_str = selected_item.text().split(" - ")[1]
            
            # Открываем диалоговое окно для ввода нового текста аннотации
            new_text, ok_text = QInputDialog.getText(self, "Редактировать аннотацию", 
                                                    "Введите новое описание аннотации:", 
                                                    QLineEdit.Normal, current_text)
            if ok_text and new_text:
                # Открываем диалоговое окно для ввода нового времени аннотации
                new_time_str, ok_time = QInputDialog.getText(self, "Редактировать аннотацию", 
                                                            "Введите новое время аннотации (HH:MM:SS):", 
                                                            QLineEdit.Normal, current_time_str)
                if ok_time:
                    try:
                        # Разбираем введенное время в секунды
                        hours, minutes, seconds = map(int, new_time_str.split(":"))
                        new_onset = hours * 3600 + minutes * 60 + seconds

                        # Извлекаем индекс выбранной аннотации
                        index = self.annotation_list.currentRow()

                        # Обновляем текст и время аннотации в raw-данных
                        self.raw.annotations.description[index] = new_text
                        self.raw.annotations.onset[index] = new_onset

                        # Обновляем отображение в списке аннотаций
                        updated_item_text = f"{new_text} - {new_time_str}"
                        self.annotation_list.item(index).setText(updated_item_text)

                        # Обновляем графическое отображение
                        self.plot_annotations()
                    except ValueError:
                        QMessageBox.warning(self, "Ошибка ввода", "Неправильный формат времени. Введите время в формате HH:MM:SS.")

    def update_annotation_list(self):
        """
        Обновление списка аннотаций в пользовательском интерфейсе.
        """
        # Очищаем текущий список аннотаций
        self.annotation_list.clear()
        # Проверяем, существуют ли аннотации в raw-данных
        if not self.raw.annotations or len(self.raw.annotations) == 0:
            return  # Если аннотаций нет, завершаем выполнение функции
        
        # Получаем списки временных меток (onset) и описаний (description) аннотаций
        onsets = self.raw.annotations.onset
        descriptions = self.raw.annotations.description

        # Обходим аннотации и добавляем их в список
        for onset, description in zip(onsets, descriptions):
            # Преобразуем время onset из секунд в формат "часы:минуты:секунды"
            onset_hms = seconds_to_hms(onset)
            # Формируем текст для отображения в списке
            item_text = f"{description} - {onset_hms}"
            # Добавляем элемент в список аннотаций
            self.annotation_list.addItem(item_text)

    def plot_annotations(self):
        """
        Отрисовка аннотаций на графике в пределах видимой области времени.
        """
        # Удаление старых линий аннотаций и текста
        for item in getattr(self, "annotation_lines", []) + getattr(self, "annotation_texts", []):
            item.remove()

        self.annotation_lines = []
        self.annotation_texts = []

        # Определение области видимого времени
        start_time = self.slider.val
        end_time = start_time + 10
        # Добавление аннотации для видимых временных меток
        for onset, description in zip(self.raw.annotations.onset, self.raw.annotations.description):
            if start_time <= onset <= end_time:
                # Преобразование времени в координаты фигуры
                x_coord = (onset - start_time) / (end_time - start_time)

                # Создаем вертикальную линию через всю высоту фигуры
                line = plt.Line2D(
                    [x_coord, x_coord], [0.08, 0.96],  # Используем пропорции Figure по оси Y
                    color="purple", linestyle="--", zorder=10,
                    transform=self.figure.transFigure  # Преобразование по Figure, чтобы покрыть все оси
                )
                self.figure.add_artist(line)
                self.annotation_lines.append(line)

                # Текст аннотации по центру фигуры
                text = self.figure.text(
                    x_coord, 0.915, f"{description} \n {seconds_to_hms(onset)}",
                    color="purple", fontsize=10, ha="left", va="bottom",
                    transform=self.figure.transFigure
                )
                self.annotation_texts.append(text)
        # Обновляем отображение
        self.canvas.draw()

    def delete_annotation(self):
        """
        Удаление выбранной аннотации и связанной с ней второй аннотации.
        """
        selected_item = self.annotation_list.currentItem()
        if selected_item:
            # Получаем индекс выбранной аннотации
            index = self.annotation_list.currentRow()

            # Находим соответствующий индекс пары
            paired_index = index + 1 if index % 2 == 0 else index - 1

            # Создаем новый список аннотаций, исключая выбранную и связанную с ней
            new_onset = np.delete(self.raw.annotations.onset, [index, paired_index])
            new_duration = np.delete(self.raw.annotations.duration, [index, paired_index])
            new_description = np.delete(self.raw.annotations.description, [index, paired_index])

            # Обновляем аннотации
            self.raw.set_annotations(mne.Annotations(new_onset, new_duration, new_description))

            # Обновляем список аннотаций в интерфейсе
            self.update_annotation_list()
            self.plot_annotations()

    def add_annotations(self):
        """
        Добавление двух новых аннотаций.
        """
        if self.raw is None:
            QMessageBox.warning(self, "Ошибка", "Не загружен EDF-файл. Сначала загрузите файл.")
            return

        # Запрос описания первой аннотации
        text1, ok1 = QInputDialog.getText(self, "Добавить аннотацию", 
                                        "Введите описание для первой аннотации:")
        if ok1 and text1:
            # Запрос времени для первой аннотации
            time_str1, ok_time1 = QInputDialog.getText(self, "Добавить аннотацию", 
                                                    "Введите время для первой аннотации (HH:MM:SS):")
            if ok_time1:
                try:
                    hours1, minutes1, seconds1 = map(int, time_str1.split(":"))
                    onset1 = hours1 * 3600 + minutes1 * 60 + seconds1
                except ValueError:
                    QMessageBox.warning(self, "Ошибка ввода", "Неправильный формат времени. Введите время в формате HH:MM:SS.")
                    return
            else:
                return

            # Запрос описания второй аннотации
            text2, ok2 = QInputDialog.getText(self, "Добавить аннотацию", 
                                            "Введите описание для второй аннотации:")
            if ok2 and text2:
                # Запрос времени для второй аннотации
                time_str2, ok_time2 = QInputDialog.getText(self, "Добавить аннотацию", 
                                                        "Введите время для второй аннотации (HH:MM:SS):")
                if ok_time2:
                    try:
                        hours2, minutes2, seconds2 = map(int, time_str2.split(":"))
                        onset2 = hours2 * 3600 + minutes2 * 60 + seconds2
                    except ValueError:
                        QMessageBox.warning(self, "Ошибка ввода", "Неправильный формат времени. Введите время в формате HH:MM:SS.")
                        return
                else:
                    return

            # Добавляем аннотации в raw-данные
            self.raw.annotations.append(onset1, 0, text1)  # Добавляем первую аннотацию (длительность 0)
            self.raw.annotations.append(onset2, 0, text2)  # Добавляем вторую аннотацию (длительность 0)

            # Обновляем список аннотаций
            self.update_annotation_list()
            self.plot_annotations()

    def jump_to_annotation(self, item):
        """
        Перемещает отображение графика к выбранной аннотации.

        item : QtWidgets.QListWidgetItem\n
            Элемент списка аннотаций, содержащий описание\n
            и время аннотации в формате "description - HH:MM:SS".
        """
        # Извлекаем текст из выбранного элемента списка
        text = item.text()
        # Извлекаем строку времени onset (HH:MM:SS) и конвертируем её в секунды
        onset_time_str = text.split(" - ")[1]
        hours, minutes, seconds = map(int, onset_time_str.split(":"))
        onset_time = hours * 3600 + minutes * 60 + seconds
        # Определяем временные границы окна отображения (10 секунд)
        window_width = 10
        start_time = max(0, onset_time - window_width / 2)
        end_time = start_time + window_width
        # Обновляем положение слайдера и оси графика
        self.slider.set_val(start_time)
        self.ax.set_xlim(start_time, end_time)
        self.ax.set_ylim(-20, 20)
        # Обновляем график
        self.update_plot(start_time)
        self.button_edit_annotation.setEnabled(True)

    def init_plot(self):
        """
        Инициализация графика и отрисовка данных каналов ЭКоГ.
        """
        # Очищаем все оси графика
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.clear()

        # Получаем частоту дискретизации сигнала (sfreq) и определяем начальные и конечные сэмплы (10 секунд)
        sfreq = self.raw.info['sfreq']
        start_sample = 0
        end_sample = int(10 * sfreq)
        # Извлекаем данные каналов и временные метки
        channels = self.raw.get_data(start=start_sample, stop=end_sample)
        times = self.raw.times[start_sample:end_sample]
        # Получаем имена каналов и отображаем данные на графике
        channel_names = self.raw.ch_names[:len(channels)]
        for i, ax in enumerate([self.ax1, self.ax2, self.ax3]):
            if i < len(channels):
                # Нормализуем данные канала для лучшего отображения
                norm_channel = (channels[i] - np.mean(channels[i])) / np.max(np.abs(channels[i]))
                # Отрисовываем данные канала
                ax.plot(times, norm_channel, label=channel_names[i], color=self.channel_colors[i])
                # Устанавливаем границы оси X и Y
                ax.set_xlim(times[0], times[-1])
                ax.set_ylim(-1.5, 1.5)
                # Добавляем заголовок и форматируем ось X
                ax.set_title(f"Канал {channel_names[i]}")
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: seconds_to_hms(x)))
                # Включаем сетку и легенду
                ax.grid(True)
                ax.legend()
        # Обновляем отображение графика и добавляем аннотации
        self.canvas.draw()
        self.plot_annotations()

    def update_plot(self, val):
        """
        Обновляет отображение графика в зависимости от положения слайдера.\n

        val : float
            Текущее значение слайдера, определяющее\n
            начало отображаемого интервала времени.
        """
        # Определяем начальное и конечное время отображаемого интервала (10 секунд)
        start_time = self.slider.val
        end_time = start_time + 10
        # Получаем частоту дискретизации (sfreq) и переводим время в сэмплы
        sfreq = self.raw.info['sfreq']
        start_sample = int(start_time * sfreq)
        end_sample = int(end_time * sfreq)
        # Проверяем, чтобы конечный сэмпл не выходил за пределы данных
        if end_sample > self.raw.n_times:
            end_sample = self.raw.n_times

        # Если начальный сэмпл больше или равен конечному, выходим из функции
        if start_sample >= end_sample:
            return

        # Извлекаем временные метки и данные каналов для текущего интервала
        times = self.raw.times[start_sample:end_sample]
        channels = self.raw.get_data(start=start_sample, stop=end_sample)
        # Обновляем каждый из трёх графиков
        for i, ax in enumerate([self.ax1, self.ax2, self.ax3]):
            if i < len(channels):
                # Нормализуем данные канала (убираем среднее и делим на максимум по модулю)
                norm_channel = (channels[i] - np.mean(channels[i])) / np.max(np.abs(channels[i]))
                # Очищаем текущий график и отрисовываем новые данные
                ax.clear()
                ax.plot(times, norm_channel, label=self.raw.ch_names[i], color=self.channel_colors[i])
                # Устанавливаем границы осей
                ax.set_xlim(times[0], times[-1])
                ax.set_ylim(-1.5, 1.5)
                # Форматируем ось X для отображения времени в формате "часы:минуты:секунды"
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: seconds_to_hms(x)))
                # Добавляем легенду и включаем сетку
                ax.legend(loc="upper right")
                ax.grid(True)
        # Обновляем отображение графика и добавляем аннотации
        self.canvas.draw()
        self.plot_annotations()

    def save_file(self):
        if self.raw is not None:
            # Получаем путь для сохранения файла
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить аннотации", self.file_path, "Все файлы (*.*)")

            if file_path:
                # Получаем имя файла и расширение из пути
                base_name, extension = os.path.splitext(file_path)
                annotated_file_path = f"{base_name}_annotated{extension}"

                # Удаляем файл с аннотациями, если он уже существует
                if os.path.exists(annotated_file_path):
                    try:
                        os.remove(annotated_file_path)
                        print(f"Файл {annotated_file_path} был удалён.")
                    except Exception as e:
                        QMessageBox.warning(self, "Предупреждение", f"Не удалось удалить старый файл с аннотациями: {str(e)}")
                        print(f"Ошибка при удалении файла: {e}")

                # Проверяем, совпадает ли путь с исходным файлом с аннотациями
                if file_path == annotated_file_path:
                    # Если файл с аннотациями уже существует, перезаписываем его
                    try:
                        self.raw.save(annotated_file_path, overwrite=True)  # Сохраняем файл с аннотациями
                        QMessageBox.information(self, "Успех", f"Аннотации успешно перезаписаны в {annotated_file_path}")
                    except Exception as e:
                        QMessageBox.critical(self, "Ошибка", f"Не удалось перезаписать файл с аннотациями: {str(e)}")
                        print(f"Ошибка при сохранении: {e}")
                else:
                    # Если путь отличается, перемещаем файл с аннотациями в новое место
                    try:
                        # Перемещаем файл с аннотациями в новое место
                        shutil.move(self.file_path, annotated_file_path)
                        QMessageBox.information(self, "Успех", f"Аннотации успешно перемещены в {annotated_file_path}")
                    except Exception as e:
                        QMessageBox.critical(self, "Ошибка", f"Не удалось переместить файл с аннотациями: {str(e)}")
                        print(f"Ошибка при перемещении: {e}")
        os.remove("annotated_is_file.edf")

    def keyPressEvent(self, event):
            """
            Обрабатывает нажатия клавиш в окне приложения.
            Позволяет перемещать график с помощью стрелок клавиатуры (влево и вправо).
            """
            # Проверяем, какая клавиша была нажата
            if event.key() == Qt.Key_Left:
                # Если нажата клавиша влево, уменьшаем значение слайдера
                new_val = max(self.slider.val - self.step_size, self.slider.valmin)
                self.slider.set_val(new_val)
                self.update_plot(new_val)

            elif event.key() == Qt.Key_Right:
                # Если нажата клавиша вправо, увеличиваем значение слайдера
                new_val = min(self.slider.val + self.step_size, self.slider.valmax)
                self.slider.set_val(new_val)
                self.update_plot(new_val)

            elif event.key() == Qt.Key_Up:
                # Увеличение step_size
                self.step_size += 1

            elif event.key() == Qt.Key_Down:
                # Уменьшение step_size, но не ниже 1
                self.step_size = max(1, self.step_size - 1)

    def toggle_theme(self):
        """
        Переключение между светлой и темной темами.
        """
        if self.styleSheet() == "":
            # Установка темной темы
            dark_theme = """
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QLabel {
                color: #ffffff;
            }
            QListWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 10px;
                background: #2e2e2e;
            }
            QSlider::handle:horizontal {
                background: #aaaaaa;
                border: 1px solid #5c5c5c;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            """
            self.setStyleSheet(dark_theme)
            self.button_toggle_theme.setText('Сменить на светлую тему')
        else:
            # Сброс темы (возвращение к светлой теме)
            self.setStyleSheet("")
            self.button_toggle_theme.setText('Сменить тему')

app = QApplication([]) 
window = MainWindow()
window.show()
app.exec_()
