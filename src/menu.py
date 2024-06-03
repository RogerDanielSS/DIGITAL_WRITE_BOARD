import sys
import cv2
import threading
import time
from PyQt5.QtWidgets import (QDialog, QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QComboBox, QWidget, QMessageBox, QRadioButton, QButtonGroup, QHBoxLayout)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QThread

from white_board import DrawingApp

class WebcamThread(QThread):
    image_data = pyqtSignal(QImage)
    error_message = pyqtSignal(str)

    def __init__(self, camera_index):
        super().__init__()
        self.camera_index = camera_index
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.error_message.emit("Erro ao abrir a câmera")
            return

        while self.running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame.shape
                q_img = QImage(frame.data, width, height, width * channel, QImage.Format_RGB888)
                self.image_data.emit(q_img)
                time.sleep(0.03)
        cap.release()

    def stop(self):
        self.running = False
        self.wait()

class WebcamSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecione a Webcam")
        self.setFixedSize(680, 400)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        label = QLabel("Selecione a webcam:")
        layout.addWidget(label)

        self.combobox = QComboBox()
        for i in range(5):  # Tentar detectar até 5 webcams
            cap = cv2.VideoCapture(i)
            if cap.isOpened() and cap.read()[0]:
                self.combobox.addItem(f"Webcam {i}")
                cap.release()
        layout.addWidget(self.combobox)

        self.image_label = QLabel()
        layout.addWidget(self.image_label)

        self.thread = None

        self.combobox.currentIndexChanged.connect(self.on_combobox_changed)
        self.add_buttons()
        self.start_preview()

        # Configurações de estilo
        self.setStyleSheet("""
            QWidget {
                background-color: #9dcfff;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #1E90FF;
                border: none;
                color: white;
                text-align: center;
                font-size: 16px;
                padding: 10px 20px;
                margin: 4px 2px;
                border-radius: 8px;
            }
             QProgressBar {
                border: none;
                text-align: center;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 8px;
            }
        """)

    def add_buttons(self):
        button_layout = QHBoxLayout()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        self.layout().addLayout(button_layout)

    def on_combobox_changed(self):
        self.stop_preview()
        self.start_preview()

    def start_preview(self):
        self.thread = WebcamThread(self.get_selected_camera_index())
        self.thread.image_data.connect(self.update_preview)
        self.thread.error_message.connect(self.show_error_message)
        self.thread.start()

    def stop_preview(self):
        if self.thread is not None:
            self.thread.stop()
            self.thread = None

    def update_preview(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap.scaledToWidth(640))

    def show_error_message(self, message):
        QMessageBox.critical(self, "Erro", message)

    def get_selected_camera_index(self):
        active_text = self.combobox.currentText()
        if active_text:
            return int(active_text.split()[-1])
        return 0

class Menu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bem vindo a Losa Digital")
        self.setFixedSize(500, 310)

        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.selected_camera_index = 0

        button_select_webcam = QPushButton("Selecionar Webcam")
        button_select_webcam.clicked.connect(self.show_webcam_selection)
        layout.addWidget(button_select_webcam)

        label_resolution = QLabel("Resolução da imagem:")
        layout.addWidget(label_resolution)

        self.resolution_group = QButtonGroup(self)
        self.add_resolution_option("640x480", layout)
        self.add_resolution_option("800x600", layout)
        self.add_resolution_option("1280x720", layout)

        self.button_start = QPushButton("Iniciar")
        self.button_start.clicked.connect(self.start)
        layout.addWidget(self.button_start)
        # Configurações de estilo
        self.setStyleSheet("""
            QWidget {
                background-color: #9dcfff;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #1E90FF;
                border: none;
                color: white;
                text-align: center;
                font-size: 16px;
                padding: 10px 20px;
                margin: 4px 2px;
                border-radius: 8px;
            }
             QProgressBar {
                border: none;
                text-align: center;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 8px;
            }
        """)

    def add_resolution_option(self, text, layout):
        resolution_button = QRadioButton(text)
        self.resolution_group.addButton(resolution_button)
        layout.addWidget(resolution_button)

    def show_webcam_selection(self):
        dialog = WebcamSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_camera_index = dialog.get_selected_camera_index()
            print(f"Webcam selecionada: {self.selected_camera_index}")
            dialog.stop_preview()

    def start(self):
        self.stop_all_threads()  # Ensure all threads are stopped before starting a new session
        selected_resolution = self.get_selected_resolution()
        print(f"Resolução selecionada: {selected_resolution}")
        self.app = DrawingApp(selected_resolution, self.selected_camera_index)
        if self.app.cap.isOpened():
            self.app.show()
            self.hide()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível acessar a câmera. Verifique se está conectada e tente novamente.")

    def stop_all_threads(self):
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, WebcamSelectionDialog):
                widget.stop_preview()
    
    def closeEvent(self, event):
        if hasattr(self, 'app') and self.app:
            self.app.stop_all_threads()
        event.accept()

    def get_selected_resolution(self):
        resolutions = [(640, 480), (800, 600), (1280, 720)]
        for i, button in enumerate(self.resolution_group.buttons()):
            if button.isChecked():
                return resolutions[i]
        return resolutions[0]
