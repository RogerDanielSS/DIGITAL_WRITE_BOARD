import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from white_board import DrawingApp

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

    def start(self, button):
        print("Iniciar pressionado")
        self.app = DrawingApp(self.resolution)
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



