import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QLabel, QToolBar,QMessageBox
from PyQt5.QtGui import QImage, QPixmap, QColor, QIcon
from PyQt5.QtCore import QTimer, Qt, QPoint

import threading
import time

from CustomMessageBox import CustomMessageBox
from PDFLoaderThread import PDFLoaderThread

def rgb_to_hex(rgb):
    return '#{0:02x}{1:02x}{2:02x}'.format(*rgb)

class WebcamWindow(QMainWindow):
    def __init__(self, cap, resolution):
        super().__init__()
        self.setWindowTitle("Webcam")
        self.setGeometry(100, 100, resolution[0], resolution[1])
        self.cap = cap
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        

        self.label = QLabel(self)
        self.setCentralWidget(self.label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_gui)
        self.timer.start(100)

        self.thread = threading.Thread(target=self.update_frame)
        self.thread.start()

    def update_frame(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame.copy()
            time.sleep(0.1)

    def refresh_gui(self):
        if self.frame is not None:
            frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio)
            self.label.setPixmap(QPixmap.fromImage(p))

    def stop_all_threads(self):
        self.running = False
        self.thread.join()

    def closeEvent(self, event):
        self.stop_all_threads()
        event.accept()

class DrawingApp(QMainWindow):
    def __init__(self, resolution, camera_index):
        super().__init__()
        self.setWindowTitle("Desenho com OpenCV e PyQt5")
        self.setGeometry(100, 100, 1024, 768)
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.progess= CustomMessageBox()
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        self.cap_resolution = resolution

        self.toolbar = self.addToolBar("Toolbar")
        

        def add_action_with_icon(icon_name, text, callback):
            icon_path = os.path.join(scriptDir, 'view', icon_name)
            if os.path.exists(icon_path):
                action = QAction(QIcon(icon_path), text, self)
                action.triggered.connect(callback)
                self.toolbar.addAction(action)
            else:
                print(f"Icon {icon_path} not found.")

        add_action_with_icon('new.png', "Novo arquivo", self.on_clear)
        add_action_with_icon('save.png', "Salvar arquivo", self.on_save)
        add_action_with_icon('webcam.png', "Abrir/Fechar(WebCam)", self.toggle_webcam)
        add_action_with_icon('pdf.png', "Inserir PDF", self.on_insert_pdf)
        add_action_with_icon('prev.png', "Voltar", self.prev_page)
        add_action_with_icon('next.png', "Avançar", self.next_page)

        self.color_buttons = [
            (0, 0, 255),  # Azul
            (0,100,0),  # Verde
            (128, 0, 128),  # Roxo
            (255, 0, 0),  # Vermelho
            (255, 69, 0),  # Laranja
            (238, 130, 238),  # Violeta
            (47,79,79), #DarkSlateGray
            (139,69,19), #SaddleBrown
            (0, 0, 0)  # Preto
        ]

        for color in self.color_buttons:
            color_action = QAction(self.create_color_icon(color), "", self)
            color_action.triggered.connect(lambda checked, col=color: self.change_color(col))
            self.toolbar.addAction(color_action)

        self.canvas = QLabel(self)
        self.setCentralWidget(self.canvas)

        self.mouse_pos = QPoint()
        self.last_mouse_pos = None
        self.drawing = False
        self.image = np.ones((768, 1024, 3), dtype=np.uint8) * 255
        self.draw_color = (0, 100, 0)

        self.pdf_pages = []
        self.current_page_index = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_gui)
        self.timer.start(100)

        self.webcam_window = WebcamWindow(self.cap, resolution)

        self.thread = threading.Thread(target=self.update_frame)
        self.thread.start()

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
            QProgressBar::chunk {
                background-color: #1E90FF; /* Cor da barra de progresso */
                width: 10px; /* Largura da barra de progresso */
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1C86EE;
            }
        """)

    def create_color_icon(self, color):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(*color))
        return QIcon(pixmap)

    def on_insert_pdf(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo PDF", "", "PDF Files (*.pdf)", options=options)
        if file_name:
            self.load_pdf(file_name)
    
    def show_progress_bar(self):
        self.progress = CustomMessageBox(self)  
        self.progress.setWindowTitle("Carrengando arquivo")
        self.progress.setText("Por favor, espere enquanto o arquivo está sendo carregado...")
        self.progress.show_progress_bar() 
        self.progress.setStandardButtons(QMessageBox.Cancel)
        self.progress.setGeometry(200, 300, 600, 600)
        self.progress.show()
         

    def load_pdf(self, pdf_path):
        self.show_progress_bar()
        self.pdf_loader_thread = PDFLoaderThread(pdf_path)
        self.pdf_loader_thread.pdf_loaded.connect(self.on_pdf_loaded)
        self.pdf_loader_thread.progress.connect(self.update_progress)
        self.pdf_loader_thread.start()

    def update_progress(self, value):
        self.progress.set_progress_value(value)


    def on_pdf_loaded(self, pages):
        self.progress.hide_progress_bar()
        self.progress.accept() 
        self.pdf_pages = pages
        self.current_page_index = 0
        self.display_page(self.current_page_index)

    def display_page(self, page_index):
        if self.pdf_pages:
            pdf_image = np.array(self.pdf_pages[page_index])
            pdf_image_resized = cv2.resize(pdf_image, (1024, 768))
            self.image = pdf_image_resized
            self.refresh_canvas()

    def prev_page(self):
        if self.pdf_pages and self.current_page_index > 0:
            self.current_page_index -= 1
            self.display_page(self.current_page_index)

    def next_page(self):
        if self.pdf_pages and self.current_page_index < len(self.pdf_pages) - 1:
            self.current_page_index += 1
            self.display_page(self.current_page_index)

    def toggle_webcam(self):
        if self.webcam_window.running:
            self.webcam_window.running = False
            self.webcam_window.thread.join()
            self.webcam_window.hide()
        else:
            self.webcam_window = WebcamWindow(self.cap, self.cap_resolution)
            self.webcam_window.show()

    def change_color(self, color):
        self.draw_color = color

    def on_clear(self):
        self.image = np.ones((768, 1024, 3), dtype=np.uint8) * 255
        self.refresh_canvas()

    def on_save(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)", options=options)
        if file_name:
            if not (file_name.endswith('.png') or file_name.endswith('.jpg')):
                file_name += '.png'  # default to PNG if no extension is provided
            cv2.imwrite(file_name, self.image)

    def refresh_canvas(self):
        h, w, _ = self.image.shape
        bytes_per_line = w * 3
        image = QImage(self.image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.canvas.setPixmap(QPixmap.fromImage(image))

    def update_frame(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = cv2.resize(frame, (640, 480))
            time.sleep(0.03)

    def detect_laser(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_val = np.array([0, 0, 200])
        upper_val = np.array([180, 55, 255])
        mask = cv2.inRange(hsv, lower_val, upper_val)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) > 500:
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    return (cX, cY)
        return None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right or event.key() == Qt.Key_Down or event.key() == Qt.Key_PageUp:
            self.next_page()
        elif event.key() == Qt.Key_Left or event.key() == Qt.Key_Up or event.key() == Qt.Key_PageDown:
            self.prev_page()

    def process_frame(self):
        if self.frame is not None:
            with self.lock:
                processed_frame = self.frame.copy()

            laser_pos = self.detect_laser(processed_frame)
            if laser_pos:
                cX, cY = laser_pos
                self.mouse_pos = QPoint(cX, cY)
                if self.last_mouse_pos:
                    cv2.line(self.image, (self.last_mouse_pos.x(), self.last_mouse_pos.y()), (self.mouse_pos.x(), self.mouse_pos.y()), self.draw_color, 3)
                self.last_mouse_pos = self.mouse_pos
            else:
                self.last_mouse_pos = None

    def refresh_gui(self):
        self.process_frame()
        self.refresh_canvas()

    def stop_all_threads(self):
        self.running = False
        self.thread.join()
        self.cap.release()
        self.webcam_window.close()
        self.webcam_window.stop_all_threads()

    def closeEvent(self, event):
        self.stop_all_threads()
        event.accept()


