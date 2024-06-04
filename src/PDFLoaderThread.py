from PyQt5.QtCore import QThread, pyqtSignal
from pdf2image import convert_from_path
import time
from PyPDF2 import PdfFileReader
import camelot
import os

class PDFLoaderThread(QThread):
    pdf_loaded = pyqtSignal(list)
    progress = pyqtSignal(int)

    def __init__(self, pdf_path):
        super().__init__()
        self.pdf_path = pdf_path
    
    def page_to_image(self, page, dpi=200):
        images = convert_from_path(page, dpi=dpi)
        return images[0] 

    def run(self):
        # Garantir que o nome do arquivo seja uma string
        pdf_file_path = str(self.pdf_path)
        # Verificar se o arquivo existe
        if not os.path.exists(pdf_file_path):
            print(f"Arquivo PDF não encontrado: {pdf_file_path}")
            return
        
        # Usar PyPDF2 para obter o número total de páginas
        with open(pdf_file_path, 'rb') as file:
            pdf_reader = PdfFileReader(file)
            total_pages = pdf_reader.numPages
        
        loaded_pages = []

        for i in range(total_pages):
            # Supondo que você tenha uma função para extrair a página individual como uma imagem
            image = self.extract_page_as_image(pdf_file_path, i)
            loaded_pages.append(image)
            progress_percent = int((i + 1) / total_pages * 100)
            self.progress.emit(progress_percent)
            time.sleep(0.1)  # Adicionar um pequeno atraso para simular o carregamento

        self.pdf_loaded.emit(loaded_pages)

    def extract_page_as_image(self, pdf_file_path, page_number, dpi=200):
        # Extrair a página como imagem usando pdf2image
        images = convert_from_path(pdf_file_path, first_page=page_number + 1, last_page=page_number + 1, dpi=dpi)
        return images[0]
