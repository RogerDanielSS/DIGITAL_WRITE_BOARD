Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

choco install python

python.exe -m pip install --upgrade pip

pip install opencv-python

pip install PyQt5

pip install pdf2image

pip install PyPDF2

pip install camelot-py[cv]

// follow GTK installation steps: https://www.gtk.org/docs/installations/windows/