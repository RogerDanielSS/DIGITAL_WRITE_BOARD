import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
from white_board import DrawingApp

class Menu(Gtk.Window):
    def __init__(self):
        super().__init__(title="Bem vindo a Losa digital")
        self.set_default_size(400, 200)

        vbox = Gtk.VBox()
        vbox.set_margin_top(10)  
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(10)  
        vbox.set_margin_end(10) 
        self.add(vbox)


        # Botão para apagar
        self.clear_button = Gtk.Button(label="Iniciar")
        self.clear_button.connect("clicked", self.start)
        self.clear_button.set_size_request(150, 50)  
        vbox.pack_start(self.clear_button, False, False, 0)


    
    def start(self):
        pass
    




