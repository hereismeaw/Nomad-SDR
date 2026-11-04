@echo off
cd /d "%~dp0"
python host\nomad_rtl_tcp.py --serial COM3 --radio 0 --port 1234
pause
