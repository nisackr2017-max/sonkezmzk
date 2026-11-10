@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul
title Lonca Music - Railway Hazirlik Kontrolu
cd /d "%~dp0"

echo ============================================
echo   LONCA MUSIC - RAILWAY HAZIRLIK KONTROLU
echo ============================================
echo.
echo Kontrol listesi:
echo   [1] MongoDB Atlas -^> Network Access -^> 0.0.0.0/0 ekli olmali
echo   [2] Bot ve Asistan hesap log grubunda uye ve ADMIN olmali
echo   [3] PO_TOKEN ve Cookie doldurmana gerek yok ^(Otomatik PO Token aktif^)
echo.

set "PY="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
if not defined PY (
    echo HATA: Python bulunamadi, config.py kontrol edilemedi.
    goto skipcheck
)

%PY% -c "import base64, struct, compileall; from config import Config; c=Config(); m=c.missing(); s=(c.SESSION1 or ''); ok=compileall.compile_dir('KumsalTR', quiet=1); raw=base64.urlsafe_b64decode(s + '='*(-len(s)%%4)) if len(s)>50 else b''; is_bot=bool(struct.unpack('>BI?256sQ?', raw)[-1]) if len(raw)==271 else False; print('KOD KONTROLU : BASARILI (Sifir Syntax Hatasi)' if ok else 'KOD KONTROLU : HATA VAR!'); print('ZORUNLU ALAN : ' + ('EKSIK -> ' + ', '.join(m) if m else 'TAMAM (Hepsi Dolu)')); print('ASISTAN SESS : ' + ('HATA! Bu bir BOT sessioni! Asistan normal telefon numarali hesap olmali (session_al.bat calistir)' if is_bot else (f'TAMAM (Normal Kullanici Hesabi, Uzunluk: {len(s)})' if len(s) > 50 else 'BOS (session_al.bat calistir veya botta /sessional kullan)')))"
if errorlevel 1 (
    echo HATA: config.py okunamadi. Once kurulum.bat calistirin.
)
echo.

:skipcheck
if exist "session_cikti.txt" (
    echo UYARI: session_cikti.txt dosyasi mevcut. GitHub'a yuklemeden once silebilirsiniz.
) else (
    echo BILGI: session_cikti.txt yok ^(Guvenli^).
)
echo.
echo Her sey tamamsa GitHub'a yukleyip Railway uzerinde Deploy edebilirsiniz!
echo.
pause
endlocal
