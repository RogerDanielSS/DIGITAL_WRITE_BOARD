import sys
from menu import Menu
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Menu()
    window.show()
    
    def handle_exit():
        if hasattr(window, 'app') and window.app:
            window.app.stop_all_threads()
    
    app.aboutToQuit.connect(handle_exit)
    sys.exit(app.exec_())
