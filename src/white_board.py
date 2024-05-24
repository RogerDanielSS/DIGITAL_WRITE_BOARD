import cv2
import numpy as np
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

class DrawingApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Desenho com OpenCV e GTK")
        self.set_default_size(800, 600)
        
        vbox = Gtk.VBox()
        self.add(vbox)
        
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(800, 600)
        self.canvas.connect("draw", self.on_draw)
        vbox.pack_start(self.canvas, True, True, 0)
        
        self.clear_button = Gtk.Button(label="Apagar")
        self.clear_button.connect("clicked", self.on_clear)
        vbox.pack_start(self.clear_button, False, False, 0)
        
        self.mouse_pos = (0, 0)
        self.last_mouse_pos = None
        self.drawing = False
        self.image = np.ones((600, 800, 3), dtype=np.uint8) * 255  # Fundo branco
        
        self.cap = cv2.VideoCapture(0)
        GLib.idle_add(self.update_frame)
        
        self.show_all()
    
    def on_clear(self, widget):
        self.image = np.ones((600, 800, 3), dtype=np.uint8) * 255  # Fundo branco
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
        ret, frame = self.cap.read()
        if ret:
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
                            cv2.line(self.image, self.last_mouse_pos, self.mouse_pos, (255,0,0), 3)
                        self.last_mouse_pos = self.mouse_pos
                    else:
                        self.last_mouse_pos = None
                else:
                    self.last_mouse_pos = None
            else:
                self.last_mouse_pos = None
            
            self.canvas.queue_draw()
        return True

    def on_destroy(self, widget):
        self.cap.release()
        Gtk.main_quit()

app = DrawingApp()
app.connect("destroy", app.on_destroy)
Gtk.main()
