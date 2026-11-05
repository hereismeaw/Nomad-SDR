@echo off
cd /d "%~dp0"
python host\nomad_api.py --serial COM3
pause
