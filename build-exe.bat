@echo off


@echo off
REM Remove as pastas dist e build, se existirem
echo Remove Old Files.....
IF EXIST dist (
    rmdir /S /Q dist
)
IF EXIST build (
    rmdir /S /Q build
)
REM Compila o script com PyInstaller
pyinstaller ./main.py --icon=spotpress.ico --noconsole --add-data "spotpress.png;."
pyinstaller ./spotpressctl.py --icon=spotpress.ico

REM Verifica se o build foi bem-sucedido
IF EXIST ".\dist\main\main.exe" (
    echo Reorganizing files
    move /Y ".\dist\main" ".\dist\spotpress"
    move /Y ".\dist\spotpress\main.exe" ".\dist\spotpress\spotpress.exe"
    move /Y ".\dist\spotpressctl\spotpressctl.exe" ".\dist\spotpress\spotpressctl.exe"
) ELSE (
    echo ERROR: File main.exe not found!
)

