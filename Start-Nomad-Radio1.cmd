@echo off
cd /d "%~dp0"
python host\nomad_rtl_tcp.py --host 192.168.4.1 --radio 1 --port 1235 --frequency 2440000000
pause
