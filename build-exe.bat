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

REM Verifica se o build foi bem-sucedido
IF EXIST ".\dist\main\main.exe" (
    echo Renaming main.exe to spotpress.exe
    move /Y ".\dist\main\main.exe" ".\dist\main\spotpress.exe"
) ELSE (
    echo ERROR: File main.exe not found!
)

