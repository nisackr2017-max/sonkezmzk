@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul
title Lonca Music - Windows Kurulum
cd /d "%~dp0"

echo ============================================
echo   LONCA MUSIC - WINDOWS KURULUM
echo   (SESSION almak + Railway'e hazirlamak)
echo ============================================
echo.
echo Not: Bot Railway uzerinde 7/24 calisir.
echo Ayarlar config.py (veya Railway Variables) icine yazilir.
echo.

set "PY="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
if not defined PY goto nopython

echo Bulunan Python surumu:
%PY% --version
echo.

echo [1/4] pip guncelleniyor...
%PY% -m pip install -U pip --quiet
echo.

echo [2/4] Eski pyrogram kaldiriliyor (kurigram ile cakismasin)...
%PY% -m pip uninstall -y pyrogram >nul 2>nul
echo.

echo [3/4] Zorunlu SESSION ve yapilandirma paketleri kuruluyor...
%PY% -m pip install -U kurigram python-dotenv aiohttp pillow
if errorlevel 1 goto piperror
echo Opsiyonel hizlandirici (pytgcrypto) deneniyor...
%PY% -m pip install -U pytgcrypto >nul 2>nul
echo.

echo [4/4] Tum bot gereksinimleri (requirements.txt) kuruluyor...
%PY% -m pip install -U -r requirements.txt
if errorlevel 1 (
    echo.
    echo UYARI: Bazi yerel ses paketleri Windows uzerinde derlenemedi.
    echo Sorun degil: SESSION alma ^(session_al.bat^) ve Railway kontrolu hazir!
    echo Railway Docker icinde tum paketler otomatik kurulur.
)
echo.

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo BILGI: Bu bilgisayarda ffmpeg bulunamadi. Railway Docker'da zaten kurulu gelir.
) else (
    echo ffmpeg bulundu.
)
echo.
echo ============================================
echo  SIRADAKI ADIMLAR
echo ============================================
echo  1^) config.py dosyasini ac ve su alanlari doldur:
echo      API_ID  API_HASH  BOT_TOKEN  MONGO_URL
echo      LOGGER_ID  OWNER_ID
echo  2^) session_al.bat calistir ^(SESSION otomatik config.py'ye yazilir^)
echo  3^) railway-hazir.bat ile ayarlarin eksiksiz oldugunu dogrula
echo  4^) PO_TOKEN bos birak ^(Lonca Music kendisi uretir^)
echo  5^) GitHub'a yukle ve Railway'de Deploy et!
echo ============================================
goto end

:nopython
echo HATA: Python 3.10 veya ustu bulunamadi!
echo Indirme adresi: https://www.python.org/downloads/
echo Kurarken "Add python.exe to PATH" kutusunu mutlaka isaretleyin.
goto end

:piperror
echo HATA: Temel kutuphaneler ^(kurigram / python-dotenv^) kurulamadi.
echo Internet baglantinizi kontrol edip tekrar deneyin.
goto end

:end
echo.
pause
endlocal
