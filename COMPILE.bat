@echo off
REM This script compiles the Umamusume Mod Manager using PyInstaller.

echo #######################################################
echo # Starting Umamusume Mod Manager Compilation...       #
echo #######################################################

REM Check if the required files exist
IF NOT EXIST "UMMM_compile.py" (
    echo.
    echo ERROR: UMMM_compile.py not found!
    echo Please make sure this script is in the same folder as your Python script.
    pause
    exit /b
)

IF NOT EXIST "icon.png" (
    echo.
    echo WARNING: icon.png not found. The application will not have a custom icon.
)

echo.
echo Running PyInstaller...
echo.

REM Run the PyInstaller command
pyinstaller --name "UMMM" --onefile --windowed --icon="icon.png" --add-data="icon.png;." UMMM_compile.py

echo.
echo #######################################################
echo # Compilation Finished!                               #
echo #######################################################
echo.
echo Your portable .exe can be found in the 'dist' folder.
echo.

REM Clean up PyInstaller temporary files
IF EXIST "UMMM.spec" del "UMMM.spec"
IF EXIST "build" rmdir /s /q "build"

echo Temporary files have been cleaned up.
pause