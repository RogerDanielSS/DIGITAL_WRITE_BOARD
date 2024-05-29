import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import cv2
import numpy as np
import threading
import time
from pdf2image import convert_from_path

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')

def rgb_to_hex(rgb):
    return '#{0:02x}{1:02x}{2:02x}'.format(*rgb)

class WebcamWindow(Gtk.Window):
    def __init__(self, cap, resolution):
        super().__init__(title="Webcam")
        self.set_default_size(resolution[0], resolution[1])
        self.cap = cap
        self.frame = None
        self.lock = threading.Lock()
        self.running = True

        self.webcam_area = Gtk.DrawingArea()
        self.webcam_area.set_size_request(resolution[0], resolution[1])
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
                self.frame.shape[1],
                self.frame.shape[0],
                self.frame.shape[1] * 3,
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
                    self.frame = frame.copy()
            time.sleep(0.1)

    def refresh_gui(self):
        self.webcam_area.queue_draw()
        return True

    def on_destroy(self, widget):
        self.running = False
        self.thread.join()

class DrawingApp(Gtk.Window):
    def __init__(self, resolution):
        super().__init__(title="Desenho com OpenCV e GTK")
        self.set_default_size(1024, 768)

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        self.cap_resolution = resolution

        vbox = Gtk.VBox()
        self.add(vbox)

        # Adicionar barra de ferramentas
        toolbar = Gtk.Toolbar()
        vbox.pack_start(toolbar, False, False, 0)

        new_file_button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_NEW)
        new_file_button.set_tooltip_text("Novo Arquivo")
        new_file_button.connect("clicked", self.on_clear)
        toolbar.insert(new_file_button, 0)

        save_button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_SAVE)
        save_button.set_tooltip_text("Salvar Arquivo")
        save_button.connect("clicked", self.on_save)
        toolbar.insert(save_button, 1)

        toggle_webcam_button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_MEDIA_PLAY)
        toggle_webcam_button.set_tooltip_text("Abrir/Fechar Webcam")
        toggle_webcam_button.connect("clicked", self.toggle_webcam)
        toolbar.insert(toggle_webcam_button, 2)

        insert_pdf_button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_OPEN)
        insert_pdf_button.set_tooltip_text("Inserir PDF")
        insert_pdf_button.connect("clicked", self.on_insert_pdf)
        toolbar.insert(insert_pdf_button, 3)

        separator = Gtk.SeparatorToolItem()
        separator.set_draw(True)
        toolbar.insert(separator, 4)

        color_buttons = [
            (0, 255, 0),    # Verde
            (128, 0, 128),  # Roxo
            (255, 0, 0), # Vermelho
            (255,69,0), # Laranja
            (238,130,238), #Violeta
            (0, 0, 0)       # Preto
        ]
        self.buttons=[]
        for color in color_buttons:
            button = Gtk.ToolButton()
            color_hex = rgb_to_hex(color)
            button.set_icon_widget(Gtk.Image.new_from_pixbuf(
                GdkPixbuf.Pixbuf.new_from_data(
                    np.full((16, 16, 3), color, dtype=np.uint8).tobytes(),
                    GdkPixbuf.Colorspace.RGB,
                    False,
                    8,
                    16,
                    16,
                    16 * 3,
                    None,
                    None
                )
            ))
            button.connect("clicked", self.change_color, color)
            toolbar.insert(button, -1)
            self.buttons.append(button)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(1024, 768)
        self.canvas.connect("draw", self.on_draw)
        vbox.pack_start(self.canvas, True, True, 0)

        self.mouse_pos = (0, 0)
        self.last_mouse_pos = None
        self.drawing = False
        self.image = np.ones((768, 1024, 3), dtype=np.uint8) * 255
        self.draw_color = (0, 255, 0)

        self.thread = threading.Thread(target=self.update_frame)
        self.thread.start()

        self.webcam_window = WebcamWindow(self.cap, resolution)

        GLib.timeout_add(100, self.refresh_gui)

        self.show_all()

    def on_insert_pdf(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Selecione um arquivo PDF", 
            parent=self, 
            action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )

        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name("PDF files")
        filter_pdf.add_mime_type("application/pdf")
        dialog.add_filter(filter_pdf)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            pdf_path = dialog.get_filename()
            self.insert_pdf_to_canvas(pdf_path)
        
        dialog.destroy()

    def insert_pdf_to_canvas(self, pdf_path):
        from pdf2image import convert_from_path
        pages = convert_from_path(pdf_path, dpi=200)
        if pages:
            pdf_image = np.array(pages[0])
            pdf_image_resized = cv2.resize(pdf_image, (1024, 768))
            self.image = cv2.addWeighted(self.image, 0.5, pdf_image_resized, 0.5, 0)

        self.canvas.queue_draw()

    def toggle_webcam(self, widget):
        if self.webcam_window.running:
            self.webcam_window.running = False
            self.webcam_window.thread.join()
            self.webcam_window.hide()
        else:
            self.webcam_window = WebcamWindow(self.cap, self.cap_resolution)
            self.webcam_window.show_all()

    def change_color(self, widget, color):
        self.draw_color = color

    def on_clear(self, widget):
        self.image = np.ones((768, 1024, 3), dtype=np.uint8) * 255
        self.canvas.queue_draw()

    def on_save(self, widget):
        # Implementar a lógica para salvar o desenho
        pass

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
        self.cap.release()
        Gtk.main_quit()

def rgb_to_hex(color):
    return '#{:02x}{:02x}{:02x}'.format(*color)


    

