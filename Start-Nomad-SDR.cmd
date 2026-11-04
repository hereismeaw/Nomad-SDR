@echo off
cd /d "%~dp0"
python host\nomad_rtl_tcp.py --host 192.168.4.1 --radio 0 --port 1234
pause
