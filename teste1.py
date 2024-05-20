import cv2
import numpy as np

# Inicializa a câmera
cap = cv2.VideoCapture(0)

# Cria uma imagem vazia para desenhar
canvas = None

# Variável para armazenar a posição do mouse
mouse_pos = (0,0)

# Função para capturar a posição do mouse
def draw_circle(event, x, y, flags, param):
    global mouse_pos
    if event == cv2.EVENT_MOUSEMOVE:
        mouse_pos = (x, y)

cv2.namedWindow('Imagem com local apontado')
cv2.setMouseCallback('Imagem com local apontado', draw_circle)

while True:
    # Captura frame por frame
    ret, frame = cap.read()

    # Cria o canvas do mesmo tamanho do frame
    if canvas is None:
        canvas = np.zeros_like(frame)

    # Desenha um círculo na posição do mouse com linha mais fina
    cv2.circle(canvas, mouse_pos, 5, (0, 255, 0), -1)

    # Combina a imagem da câmera e o canvas
    combo = cv2.add(frame, canvas)

    # Exibe o resultado
    cv2.imshow('Imagem com local apontado', combo)

    # Se 'q' for pressionado, sai do loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Quando tudo estiver pronto, libera a captura e destrói todas as janelas
cap.release()
cv2.destroyAllWindows()
