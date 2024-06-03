from PyQt5.QtCore import  QThread, pyqtSignal
from pdf2image import convert_from_path

class PDFLoaderThread(QThread):
    pdf_loaded = pyqtSignal(list)

    def __init__(self, pdf_path):
        super().__init__()
        self.pdf_path = pdf_path

    def run(self):
        pages = convert_from_path(self.pdf_path, dpi=200)
        self.pdf_loaded.emit(pages)