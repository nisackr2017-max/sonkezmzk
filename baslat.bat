@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul
title Lonca Music - Yerel Baslatici
cd /d "%~dp0"

echo ============================================
echo   LONCA MUSIC BASLATILIYOR...
echo ============================================
echo.
echo DIKKAT: Bot Railway'de calisiyorsa burada AYNI ANDA calistirmayin!
echo Ayni SESSION iki yerde acilirsa Telegram onu iptal eder ^(AUTH_KEY_DUPLICATED^)
echo ve yeni SESSION almaniz gerekir. Once Railway'de servisi durdurun.
echo.
choice /C EH /M "Railway'deki bot kapali mi, devam edilsin mi (E=Evet, H=Hayir)"
if errorlevel 2 exit /b 0
echo.

set "PY="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
if not defined PY (
    echo HATA: Python 3.10+ bulunamadi! Once kurulum.bat calistirin.
    pause
    exit /b 1
)

%PY% -m KumsalTR
echo.
echo Bot durdu. Kapatmak icin bir tusa basin...
pause
endlocal

