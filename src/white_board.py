import cv2
import numpy as np
import gi
import threading
import time
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

def rgb_to_hex(rgb):
    return '#{0:02x}{1:02x}{2:02x}'.format(*rgb)


class WebcamWindow(Gtk.Window):
    def __init__(self, cap):
        super().__init__(title="Webcam")
        self.set_default_size(640, 480)
        self.cap = cap
        self.frame = None
        self.lock = threading.Lock()
        self.running = True

        self.webcam_area = Gtk.DrawingArea()
        self.webcam_area.set_size_request(640, 480)
        self.webcam_area.connect("draw", self.on_draw)
        self.add(self.webcam_area)

        self.thread = threading.Thread(target=self.update_frame)
        self.thread.start()

        GLib.timeout_add(100, self.refresh_gui)  # Atualiza a cada 100 ms

        self.show_all()

    def on_draw(self, widget, cr):
        if self.frame is not None:
            frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                frame.tobytes(),
                GdkPixbuf.Colorspace.RGB,
                False,
                8,
                640,
                480,
                640 * 3,
                None,
                None
            )
            Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
            cr.paint()

    def update_frame(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame.copy()
            time.sleep(0.03)

    def refresh_gui(self):
        self.webcam_area.queue_draw()
        return True

    def on_destroy(self, widget):
        self.running = False
        self.thread.join()

class DrawingApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Desenho com OpenCV e GTK")
        self.set_default_size(800, 600)

        vbox = Gtk.VBox()
        vbox.set_margin_top(10)  # Adicionando margem superior
        vbox.set_margin_bottom(10)  # Adicionando margem inferior
        vbox.set_margin_start(10)  # Adicionando margem à esquerda
        vbox.set_margin_end(10)  # Adicionando margem à direita
        self.add(vbox)
        
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(800, 600)
        self.canvas.connect("draw", self.on_draw)
        vbox.pack_start(self.canvas, True, True, 0)
        
        # Usando um grid para organizar os botões
        button_grid = Gtk.Grid()
        button_grid.set_row_spacing(10)
        button_grid.set_column_spacing(10)
        # Criando um Gtk.Box para os botões de cores
        color_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        color_buttons_box.set_center_widget(button_grid)  # Centralizando os botões de cores
        vbox.pack_start(color_buttons_box, False, False, 0)

        button_labels_colors = [
            ("Vermelho", (255, 0, 0)),
            ("Azul", (0, 0, 255)),
            ("Verde", (0, 255, 0)),
            ("Marrom", (150, 75, 0)),
            ("laranja", (255, 140, 0)),
            ("Preto", (0, 0, 0)),
        ]

        # Criando os botões e conectando-os ao método change_color
        self.buttons = []
        for i, (label, color) in enumerate(button_labels_colors):
            button = Gtk.Button(label=label)
            button.set_size_request(100, 50)
            button.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse(rgb_to_hex(color)))
            button.connect("clicked", self.change_color, color)
            button_grid.attach(button, i, 0, 1, 1)
            self.buttons.append(button)
        vbox.pack_start(Gtk.Label(), False, False, 2)
        # Botão para apagar
        self.clear_button = Gtk.Button(label="Apagar")
        self.clear_button.connect("clicked", self.on_clear)
        self.clear_button.set_size_request(150, 50)  # Ajustando o tamanho do botão
        vbox.pack_start(self.clear_button, False, False, 0)

        # Adicionando margem entre o botão Apagar e os botões de cores
        vbox.pack_start(Gtk.Label(), False, False, 1)

        # Botão para abrir/fechar a webcam
        self.toggle_webcam_button = Gtk.Button(label="Abrir/fechar Web Cam")
        self.toggle_webcam_button.connect("clicked", self.toggleWebCam)
        self.toggle_webcam_button.set_size_request(250, 50)  # Ajustando o tamanho do botão
        vbox.pack_start(self.toggle_webcam_button, False, False, 0)

        # Adicionando margem entre os botões de cores e o botão Abrir/fechar Web Cam
        vbox.pack_start(Gtk.Label(), False, False, 1)

        self.mouse_pos = (0, 0)
        self.last_mouse_pos = None
        self.drawing = False
        self.image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        self.draw_color = (0, 0, 255)

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        
        self.thread = threading.Thread(target=self.update_frame)
        self.thread.start()
        
        GLib.timeout_add(50, self.refresh_gui)

        self.webcam_window = WebcamWindow(self.cap)

        self.show_all()
        

    def create_color_button(self, label, color, box):
        button = Gtk.Button(label=label)
        button.connect("clicked", self.change_color, color)
        box.pack_start(button, False, False, 0)

    def change_color(self, widget, color):
        self.draw_color = color
    

    def toggleWebCam(self, widget):
        if self.webcam_window.running:
            self.webcam_window.running = False
            self.webcam_window.thread.join()
            self.webcam_window.hide()
        else:
            self.webcam_window = WebcamWindow(self.cap)
        

    def on_clear(self, widget):
        self.image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        self.canvas.queue_draw()

    def on_draw(self, widget, cr):
        h, w, _ = self.image.shape
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            self.image.tobytes(),
            GdkPixbuf.Colorspace.RGB,
            False,
            8,
            w,
            h,
            w * 3,
            None,
            None
        )
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
        cr.paint()

    def update_frame(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = cv2.resize(frame, (640, 480))
            time.sleep(0.03)

    def process_frame(self):
        if self.frame is not None:
            with self.lock:
                frame = self.frame.copy()
            
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower_red = np.array([0, 120, 70])
            upper_red = np.array([10, 255, 255])
            mask1 = cv2.inRange(hsv, lower_red, upper_red)

            lower_red = np.array([170, 120, 70])
            upper_red = np.array([180, 255, 255])
            mask2 = cv2.inRange(hsv, lower_red, upper_red)

            mask = mask1 + mask2

            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 1000:
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        self.mouse_pos = (cX, cY)
                        if self.last_mouse_pos is not None:
                            cv2.line(self.image, self.last_mouse_pos, self.mouse_pos, self.draw_color, 3)
                        self.last_mouse_pos = self.mouse_pos
                    else:
                        self.last_mouse_pos = None
                else:
                    self.last_mouse_pos = None
            else:
                self.last_mouse_pos = None

    def refresh_gui(self):
        self.process_frame()
        self.canvas.queue_draw()
        return True

    def on_destroy(self, widget):
        self.running = False
        self.thread.join()
        self.webcam_window.running = False
        self.webcam_window.thread.join()
        self.cap.release()
        Gtk.main_quit()

app = DrawingApp()
app.connect("destroy", app.on_destroy)
Gtk.main()
