@echo off
mode con: cols=95 lines=20
color A1
cls
@echo on
@ echo:++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@ Echo: PharmApp // Copyright 2025 // NGHIEN CUU THUOC // RnD PHARMA PLUS // WWW.NGHIENCUUTHUOC.COM
@ Echo: Email: nghiencuuthuoc@gmail.com // LinkedIN: https://linkedin.com/in/nghiencuuthuoc
@ Echo: YouTube: https://youtube.com/@nghiencuuthuoc // Twitter: https://x.com/NghienCuuThuoc 
@ Echo: Zalo: +84888999311 // WhatsAapp: +84888999311 // Facebook: https://fb.com/nghiencuuthuoc
@ Echo: +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@echo off
Title  Su Co Tam Tam // PrajnaPlayer
@ECHO off
set py=%LocalAppData%\Programs\Python\Python312\python.exe
set path=%~dp0

REM cd "%~dp0\scripts" && start cmd.exe /c "%~dp0\scripts\iig_iigs_to_formula_st.bat"
REM cd "%~dp0\src" && start python.exe main.py
%py% "%~dp0src\PrajnaPlayer.py"

pause
cls
PrajnaPlayer.bat
