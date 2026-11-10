@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>nul
title Lonca Music - GitHub'a Yukle
cd /d "%~dp0"

echo ============================================
echo   LONCA MUSIC - GITHUB'A YUKLEME ARACI
echo ============================================
echo.

where git >nul 2>nul
if errorlevel 1 (
    echo HATA: Bu bilgisayarda Git kurulu degil
    echo.
    echo Git olmadan da GitHub'a yukleyebilirsiniz:
    echo  1^) Proje klasorunuzdeki dosyalari secin ve .ZIP yapin
    echo  2^) github.com sitesinde yeni bir PRIVATE repository acin
    echo  3^) "uploading an existing file" secenegiyle dosyalari surukleyip birakin
    echo.
    echo Veya Git programini kurmak isterseniz:
    echo   https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

if not exist ".git" (
    echo [1/4] Git deposu baslatiliyor...
    git init
    git branch -M main
) else (
    echo [1/4] Mevcut Git deposu kontrol ediliyor...
)
echo.

git config user.email >nul 2>nul
if errorlevel 1 (
    echo Git ilk kez kullaniliyor, kimlik bilgisi gerekli ^(sadece bir kez sorulur^).
    set /p GIT_NAME="Adiniz veya GitHub kullanici adiniz: "
    set /p GIT_MAIL="GitHub e-posta adresiniz: "
    if not defined GIT_NAME set "GIT_NAME=Lonca Music"
    if not defined GIT_MAIL set "GIT_MAIL=lonca@example.com"
    git config user.name "!GIT_NAME!"
    git config user.email "!GIT_MAIL!"
    echo.
)

echo [2/4] Dosyalar hazirlaniyor...
git add .
echo.

echo [3/4] Degisiklikler kaydediliyor...
git diff --cached --quiet
if errorlevel 1 (
    git commit -q -m "Lonca Music - Railway guncellemesi %DATE% %TIME%"
    if errorlevel 1 (
        echo HATA: Commit olusturulamadi. Yukaridaki git mesajini kontrol edin.
        pause
        exit /b 1
    )
    echo Degisiklikler kaydedildi.
) else (
    echo BILGI: Yeni degisiklik yok, mevcut surum gonderilecek.
)
echo.

echo [4/4] GitHub baglantisi kontrol ediliyor...
git remote get-url origin >nul 2>nul
if errorlevel 1 (
    echo.
    echo UYARI: Henuz bir GitHub repository baglantisi tanimlanmamis
    echo.
    echo Lutfen GitHub'da olusturdugunuz PRIVATE repository URL'sini yapistirin:
    echo ^(Ornek: https://github.com/KULLANICI_ADINIZ/lonca-music.git^)
    echo.
    set /p REPO_URL="Repo URL: "
    if not defined REPO_URL (
        echo Repo URL bos birakildi, islem iptal edildi.
        pause
        exit /b 1
    )
    git remote add origin "!REPO_URL!"
)

echo.
echo GitHub'a gonderiliyor (git push)...
git push -u origin main
if errorlevel 1 (
    echo.
    echo HATA: GitHub'a gonderilemedi
    echo Lutfen GitHub kullanici adi ve Personal Access Token sifrenizi kontrol edin.
) else (
    echo.
    echo ============================================
    echo  TEBRIKLER Kodlar GitHub'a basariyla yuklendi.
    echo  Railway otomatik olarak yeni surumu algilayip baslatacaktir.
    echo ============================================
)

echo.
pause
endlocal

