#!/bin/bash

# Atualiza os pacotes do sistema
sudo apt update && sudo apt upgrade -y

# Instala dependências do sistema
sudo apt install -y python3 python3-pip python3-venv libgtk-3-dev libopencv-dev git

# Cria e ativa um ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instala dependências Python no ambiente virtual
pip install opencv-python-headless PyGObject

# Clone o repositório do GitHub (substitua pelo URL do seu repositório)
# git clone https://github.com/seu-usuario/seu-repositorio.git
# cd seu-repositorio

# Copie os arquivos para o diretório de aplicativos padrão
sudo cp -r * /usr/local/bin/

# Cria um lançador de aplicativo (opcional)
cat << EOF > ~/Desktop/LosaDigital.desktop
[Desktop Entry]
Name=Losa Digital
Exec=/usr/local/bin/venv/bin/python /usr/local/bin/menu.py
Type=Application
Terminal=false
Icon=utilities-terminal
EOF

chmod +x ~/Desktop/LosaDigital.desktop

# Desativa o ambiente virtual
deactivate

echo "Instalação concluída. Você pode iniciar o aplicativo clicando no ícone 'Losa Digital' na área de trabalho."
