@echo off
set "NO_PAUSE="
if /I "%~1"=="nopause" set "NO_PAUSE=1"
:: =============================================================================
::  YT AZS V12.0  -  Windows EXE Builder (PyInstaller + Inno Setup)
::  Pune acest fisier in ACELASI folder cu:
::      YT-AZS.py
::      download_engines.py
::      web_server.py
::      logo_white_PNG.png
::      logo_black_PNG.png
::      YT-AZS.ico
::      requirements_ytazs.txt
::      setup_ytazs.iss          (generat automat la sfarsit)
:: =============================================================================

echo.
echo  ==========================================
echo   YT AZS V12.0  -  Windows EXE Builder
echo  ==========================================
echo.

set "PYTHON_EXE="
for /f "delims=" %%i in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
if not defined PYTHON_EXE set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo  [EROARE] Python nu a fost gasit in PATH!
    echo  Descarca Python 3.10+ de la https://python.org
    echo  si bifeaza "Add Python to PATH" la instalare.
    goto :fail
)
echo  [OK] Python gasit: %PYTHON_EXE%

if not exist "YT-AZS.py" (
    echo  [EROARE] YT-AZS.py nu a fost gasit in acest folder!
    goto :fail
)
echo  [OK] YT-AZS.py gasit.

if not exist "logo_white_PNG.png" (
    echo  [ATENTIE] logo_white_PNG.png lipsa.
) else ( echo  [OK] logo_white_PNG.png gasit. )

if not exist "logo_black_PNG.png" (
    echo  [ATENTIE] logo_black_PNG.png lipsa.
) else ( echo  [OK] logo_black_PNG.png gasit. )

if not exist "YT-AZS.ico" (
    echo  [ATENTIE] YT-AZS.ico lipsa.
) else ( echo  [OK] YT-AZS.ico gasit. )
echo.

echo  [1/5] Instalare dependinte Python...
"%PYTHON_EXE%" -m pip install --upgrade customtkinter yt-dlp imageio-ffmpeg Pillow mutagen pyinstaller
if errorlevel 1 ( echo  [EROARE] pip a esuat. & goto :fail )
echo.

echo  [2/5] Detectare cale customtkinter...
set "CTK_PATH_FILE=%TEMP%\ytazs_ctk_path.txt"
"%PYTHON_EXE%" -c "import customtkinter,os;print(os.path.dirname(customtkinter.__file__))" > "%CTK_PATH_FILE%"
if errorlevel 1 ( echo  [EROARE] customtkinter negasit. & goto :fail )
set /p CTK_PATH=<"%CTK_PATH_FILE%"
del "%CTK_PATH_FILE%" >nul 2>&1
if "%CTK_PATH%"=="" ( echo  [EROARE] customtkinter negasit. & goto :fail )
echo  [OK] %CTK_PATH%

echo  [3/5] Detectare cale imageio_ffmpeg...
set "FFMPEG_PATH_FILE=%TEMP%\ytazs_ffmpeg_path.txt"
"%PYTHON_EXE%" -c "import imageio_ffmpeg,os;print(os.path.dirname(imageio_ffmpeg.__file__))" > "%FFMPEG_PATH_FILE%"
if errorlevel 1 ( echo  [EROARE] imageio_ffmpeg negasit. & goto :fail )
set /p FFMPEG_PKG=<"%FFMPEG_PATH_FILE%"
del "%FFMPEG_PATH_FILE%" >nul 2>&1
if "%FFMPEG_PKG%"=="" ( echo  [EROARE] imageio_ffmpeg negasit. & goto :fail )
echo  [OK] %FFMPEG_PKG%

echo  [4/5] Detectare cale Pillow...
set "PIL_PATH_FILE=%TEMP%\ytazs_pil_path.txt"
"%PYTHON_EXE%" -c "import PIL,os;print(os.path.dirname(PIL.__file__))" > "%PIL_PATH_FILE%"
if errorlevel 1 ( echo  [EROARE] Pillow negasit. & goto :fail )
set /p PIL_PATH=<"%PIL_PATH_FILE%"
del "%PIL_PATH_FILE%" >nul 2>&1
if "%PIL_PATH%"=="" ( echo  [EROARE] Pillow negasit. & goto :fail )
echo  [OK] %PIL_PATH%
echo.

echo  [5/5] Construire executabil cu PyInstaller...
echo  Poate dura 2-4 minute. Te rog asteapta.
echo.

tasklist /FI "IMAGENAME eq YT-AZS.exe" 2>nul | find /I "YT-AZS.exe" >nul
if not errorlevel 1 (
    echo  [EROARE] YT AZS este inca pornit.
    echo  Inchide aplicatia YT AZS inainte de build, altfel Windows blocheaza fisierele din dist.
    goto :fail
)

"%PYTHON_EXE%" -m PyInstaller ^
  --noconfirm ^
  --onedir ^
  --windowed ^
  --name "YT-AZS" ^
  --icon "YT-AZS.ico" ^
  --add-data "logo_white_PNG.png;." ^
  --add-data "logo_black_PNG.png;." ^
  --add-data "YT-AZS.ico;." ^
  --add-data "%CTK_PATH%;customtkinter" ^
  --add-data "%FFMPEG_PKG%;imageio_ffmpeg" ^
  --add-data "%PIL_PATH%;PIL" ^
  --hidden-import "download_engines" ^
  --hidden-import "web_server" ^
  --hidden-import "customtkinter" ^
  --hidden-import "PIL._tkinter_finder" ^
  --hidden-import "PIL.Image" ^
  --hidden-import "imageio_ffmpeg" ^
  --hidden-import "yt_dlp" ^
  --collect-all "customtkinter" ^
  --collect-all "yt_dlp" ^
  YT-AZS.py

if not exist "dist\YT-AZS\YT-AZS.exe" (
    echo.
    echo  [EROARE] PyInstaller a esuat. Verifica erorile de mai sus.
    goto :fail
)
echo.
echo  [OK] PyInstaller gata: dist\YT-AZS\YT-AZS.exe
echo.

:: -- Genereaza fisierul .iss pentru Inno Setup --------------------------------
echo  Generare script Inno Setup (setup_ytazs.iss)...

set "DIST_DIR=%~dp0dist\YT-AZS"

(
echo [Setup]
echo AppName=YT AZS
echo AppVersion=12.0
echo AppId={{65A83D2B-0A45-4B52-9F58-2E548F6D9D1A}
echo AppPublisher=David Marica - AZS Gherla
echo AppPublisherURL=https://www.azsgherla.ro
echo DefaultDirName={autopf}\YT AZS
echo DefaultGroupName=YT AZS
echo OutputDir=%~dp0installer
echo OutputBaseFilename=YT-AZS-Setup-V12.0
echo Compression=lzma2/ultra64
echo SolidCompression=yes
echo WizardStyle=modern
echo UsePreviousAppDir=yes
echo CloseApplications=yes
echo RestartApplications=no
echo UninstallDisplayIcon={app}\YT-AZS.exe
echo PrivilegesRequired=lowest
echo.
echo [Languages]
echo Name: "ro"; MessagesFile: "compiler:Languages\Romanian.isl"
echo Name: "en"; MessagesFile: "compiler:Default.isl"
echo.
echo [Tasks]
echo Name: "desktopicon"; Description: "Creaza o pictograma pe Desktop"; GroupDescription: "Pictograme aditionale:"
echo.
echo [Files]
echo Source: "%DIST_DIR%\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
echo.
echo [Icons]
echo Name: "{group}\YT AZS"; Filename: "{app}\YT-AZS.exe"
echo Name: "{group}\Dezinstaleaza YT AZS"; Filename: "{uninstallexe}"
echo Name: "{commondesktop}\YT AZS"; Filename: "{app}\YT-AZS.exe"; Tasks: desktopicon
echo.
echo [Run]
echo Filename: "{app}\YT-AZS.exe"; Description: "Porneste YT AZS V12"; Flags: nowait postinstall skipifsilent
) > setup_ytazs.iss

echo  [OK] setup_ytazs.iss generat.
echo.
echo  ==========================================
echo   PASUL URMATOR: Inno Setup
echo  ==========================================
echo.
echo  1. Descarca si instaleaza Inno Setup de la:
echo     https://jrsoftware.org/isdl.php
echo.
echo  2. Deschide fisierul: setup_ytazs.iss
echo     (dublu-click pe el dupa instalare Inno Setup)
echo.
echo  3. Apasa Ctrl+F9 sau Build - Compile
echo.
echo  4. Installer-ul final va fi in:
echo     installer\YT-AZS-Setup-V12.0.exe
echo.
echo  Acesta este un .exe installer adevarat cu:
echo   - Start Menu shortcut
echo   - Optiune shortcut pe Desktop
echo   - Dezinstalare din Control Panel
echo   - Nu necesita Python instalat
echo.
goto :done

:fail
if not defined NO_PAUSE pause
exit /b 1

:done
if not defined NO_PAUSE pause
exit /b 0
