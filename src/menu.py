import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from white_board import DrawingApp
import cv2
class WebcamSelectionDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Selecione a Webcam", transient_for=parent, flags=0)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        self.set_default_size(150, 100)

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

        self.show_all()

    def get_selected_camera_index(self):
        return self.combobox.get_active()
class Menu(Gtk.Window):
    def __init__(self):
        super().__init__(title="Bem vindo a Losa Digital")
        self.set_default_size(400, 200)
        self.webcam_window = None
        self.resolution = (640, 480)

        vbox = Gtk.VBox()
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        self.add(vbox)

          # Botão para abrir a seleção de webcam
        select_webcam_button = Gtk.Button(label="Selecionar Webcam")
        select_webcam_button.connect("clicked", self.on_select_webcam)
        vbox.pack_start(select_webcam_button, False, False, 0)

        self.resolution_label = Gtk.Label(label="Resolução da imagem:")
        vbox.pack_start(self.resolution_label, False, False, 0)

        self.resolution_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vbox.pack_start(self.resolution_box, False, False, 0)

        resolutions = [("640x480", (640, 480)), ("800x600", (800, 600)), ("1280x720", (1280, 720))]

        self.resolution_buttons = []
        for label, resolution in resolutions:
            button = Gtk.RadioButton.new_with_label_from_widget(None, label)
            button.connect("toggled", self.on_resolution_selected, resolution)
            self.resolution_box.pack_start(button, False, False, 0)
            self.resolution_buttons.append(button)
        self.resolution_buttons[0].set_active(True)

        self.start_button = Gtk.Button(label="Iniciar")
        self.start_button.connect("clicked", self.start)
        self.start_button.set_size_request(150, 50)
        vbox.pack_start(self.start_button, False, False, 0)

    def on_resolution_selected(self, button, resolution):
        if button.get_active():
            self.resolution = resolution
            print("Resolução selecionada:", resolution)
    
    def on_select_webcam(self, widget):
        dialog = WebcamSelectionDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_camera_index = dialog.get_selected_camera_index()
        dialog.destroy()

    def start(self, button):
        print("Iniciar pressionado")
        self.app = DrawingApp(self.resolution,self.selected_camera_index)
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

win = Menu()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()



