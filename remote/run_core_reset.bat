@echo off
setlocal
cd /d "%~dp0"
python remote_artiq.py --config config.local.json run examples\core_reset.py
