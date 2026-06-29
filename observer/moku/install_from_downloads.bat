@echo off
setlocal
cd /d "%~dp0"
python -m pip install --no-index --find-links packages moku==4.2.2.1
