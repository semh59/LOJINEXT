import PyInstaller.__main__
import shutil
import os

# Clean previous build
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists("dist"):
    shutil.rmtree("dist")

PyInstaller.__main__.run([
    'app/main.py',
    '--name=Tiryaki',
    '--windowed',
    '--onedir',
    '--noconfirm',
    '--clean',
    '--collect-all=customtkinter',
    '--icon=NONE',
    # Include assets if they exist
    '--add-data=app/assets;app/assets',
    # Paths
    '--paths=.'
])
