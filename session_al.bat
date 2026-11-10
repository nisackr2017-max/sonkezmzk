@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul
title Lonca Music - Asistan SESSION Olusturucu
cd /d "%~dp0"

echo ============================================
echo   LONCA MUSIC - ASISTAN SESSION ALICI
echo   Cikti otomatik olarak config.py'ye yazilir
echo ============================================
echo.

set "PY="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
if not defined PY goto nopython

echo Python:
%PY% --version
echo.

%PY% -c "import pyrogram.types as t; raise SystemExit(0 if hasattr(t, 'LinkPreviewOptions') else 1)" >nul 2>nul
if not errorlevel 1 goto run

echo Gerekli kutuphaneler ^(kurigram^) kuruluyor, lutfen bekleyin...
%PY% -m pip uninstall -y pyrogram >nul 2>nul
%PY% -m pip install -U pip --quiet >nul 2>nul
%PY% -m pip install -U kurigram python-dotenv
if errorlevel 1 goto piperror
%PY% -m pip install -U pytgcrypto >nul 2>nul
echo.

:run
echo Telefon numaranizi +905xxxxxxxxx seklinde girin.
echo Telegram'a gelen kodu yazin. Iki adimli dogrulama varsa sifrenizi sorar.
echo.
%PY% session_al.py
if errorlevel 1 goto end

echo.
echo --------------------------------------------
echo  BASARILI: SESSION config.py icine yazildi!
echo  Simdi railway-hazir.bat ile kontrol edebilirsin.
echo --------------------------------------------
goto end

:nopython
echo HATA: Python 3.10 veya ustu bulunamadi!
echo https://www.python.org/downloads/
echo Kurarken "Add python.exe to PATH" kutusunu isaretleyin.
goto end

:piperror
echo HATA: kurigram kurulamadi. Internet baglantinizi kontrol edin.
echo Elle kurmak icin: %PY% -m pip install -U kurigram python-dotenv
goto end

:end
echo.
pause
endlocal
