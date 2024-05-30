import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import threading
import time
from white_board import DrawingApp
import cv2

class WebcamSelectionDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Selecione a Webcam", transient_for=parent, flags=0)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        self.set_default_size(680, 400)

        box = self.get_content_area()

        label = Gtk.Label(label="Selecione a webcam:")
        box.add(label)

        self.combobox = Gtk.ComboBoxText()
        for i in range(5):  # Tentar detectar até 5 webcams
            cap = cv2.VideoCapture(i)
            if cap is not None and cap.read()[0]:
                self.combobox.append_text(f"Webcam {i}")
                cap.release()
        self.combobox.set_active(0)
        box.add(self.combobox)

        self.image = Gtk.Image()
        box.add(self.image)

        self.show_all()

        self.running = False
        self.thread = None

        self.combobox.connect("changed", self.on_combobox_changed)
        self.connect("response", self.on_response)

        # Iniciar o preview da webcam
        self.start_preview()

    def on_combobox_changed(self, combobox):
        self.stop_preview()
        self.start_preview()

    def start_preview(self):
        self.running = True
        self.thread = threading.Thread(target=self.update_preview)
        self.thread.start()

    def stop_preview(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()

    def update_preview(self):
        selected_camera_index = self.get_selected_camera_index()
        cap = cv2.VideoCapture(selected_camera_index)
        if not cap.isOpened():
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT, self.show_error_message, "Erro ao abrir a câmera")
            return
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channels = frame.shape
                rowstride = width * channels
                pb = GdkPixbuf.Pixbuf.new_from_data(frame.tobytes(), GdkPixbuf.Colorspace.RGB, False, 8, width, height, rowstride)
                Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT, self.image.set_from_pixbuf, pb)
            time.sleep(0.03)
        cap.release()

    def show_error_message(self, message):
        dialog = Gtk.MessageDialog(parent=self, flags=0, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, text=message)
        dialog.run()
        dialog.destroy()

    def on_response(self, dialog, response):
        self.stop_preview()
        dialog.destroy()

    def get_selected_camera_index(self):
        active_text = self.combobox.get_active_text()
        if active_text:
            return int(active_text.split()[-1])
        return 0

class Menu(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Bem vindo a Losa Digital")
        self.set_default_size(500, 200)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(box)

        # Inicializar o índice da câmera selecionada com um valor padrão
        self.selected_camera_index = 0
        self.webcam_window = None

        # Botão para selecionar a webcam
        button = Gtk.Button(label="Selecionar Webcam")
        button.connect("clicked", self.on_button_clicked)
        box.add(button)

        # Opções de resolução
        resolution_label = Gtk.Label(label="Resolução da imagem:")
        box.add(resolution_label)

        self.resolution_group = Gtk.RadioButton.new_with_label_from_widget(None, "640x480")
        box.add(self.resolution_group)

        resolution_800x600 = Gtk.RadioButton.new_with_label_from_widget(self.resolution_group, "800x600")
        box.add(resolution_800x600)

        resolution_1280x720 = Gtk.RadioButton.new_with_label_from_widget(self.resolution_group, "1280x720")
        box.add(resolution_1280x720)

        # Botão iniciar
        start_button = Gtk.Button(label="Iniciar")
        start_button.connect("clicked", self.start)
        box.add(start_button)

        self.show_all()

    def on_button_clicked(self, widget):
        dialog = WebcamSelectionDialog(self)
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            self.selected_camera_index = dialog.get_selected_camera_index()
            print(f"Webcam selecionada: {self.selected_camera_index}")
        dialog.destroy()

    def on_start_button_clicked(self, widget):
        selected_resolution = self.get_selected_resolution()
        print(f"Resolução selecionada: {selected_resolution}")
        DrawingApp(selected_resolution, self.selected_camera_index)

    def get_selected_resolution(self):
        if self.resolution_group.get_active():
            return (640, 480)
        elif self.resolution_group.get_group()[1].get_active():
            return (800, 600)
        elif self.resolution_group.get_group()[2].get_active():
            return (1280, 720)
        return (640, 480)
    
    def start(self, button):
        print("Iniciar pressionado")
        selected_resolution = self.get_selected_resolution()
        print("Resolução selecionada ", selected_resolution)
        self.app = DrawingApp(selected_resolution,self.selected_camera_index)
        self.app.connect("destroy", self.on_app_destroy)
        self.app.show_all()
        self.hide()
        self.webcam_window = self.app.webcam_window

    def on_app_destroy(self, widget):
        self.app.on_destroy(widget)
        self.destroy()
        if self.webcam_window:
            self.webcam_window.running = False
            self.webcam_window.thread.join()
            self.webcam_window.destroy()

if __name__ == "__main__":
    win = Menu()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
