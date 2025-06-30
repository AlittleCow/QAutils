@echo off
REM QAUtils TDX Plugin Build Script
REM This script automates the build process for the TDX plugin

echo ==========================================
echo QAUtils TDX Plugin Build Script
echo ==========================================

REM Check if CMake is installed in the default location and add to PATH if needed
if exist "C:\Program Files\CMake\bin\cmake.exe" (
    echo Found CMake in C:\Program Files\CMake\bin
    set "PATH=C:\Program Files\CMake\bin;%PATH%"
) else (
    echo CMake not found in C:\Program Files\CMake\bin, checking PATH...
)

REM Check if CMake is available
cmake --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: CMake is not installed or not in PATH
    echo Please install CMake 3.10 or higher and add it to your PATH
    echo Expected locations:
    echo   - C:\Program Files\CMake\bin\cmake.exe
    echo   - Or add CMake to your system PATH
    pause
    exit /b 1
) else (
    echo CMake found and ready to use
    cmake --version
)

REM Create build directory
if not exist build (
    echo Creating build directory...
    mkdir build
)

cd build

REM Configure the project
echo Configuring project...
cmake .. -G "Visual Studio 17 2022" -A Win32 -DBUILD_TESTS=ON
if errorlevel 1 (
    echo ERROR: CMake configuration failed
    pause
    exit /b 1
)

REM Build the project
echo Building project (Release configuration)...
cmake --build . --config Release
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build completed successfully!
echo ==========================================
echo.
echo Output files:
echo - DLL: build\bin\Release\QAUtilsTdxPlugin.dll
echo - LIB: build\lib\Release\QAUtilsTdxPlugin.lib
echo.
echo To use with TDX:
echo 1. Copy QAUtilsTdxPlugin.dll to your TDX installation directory
echo 2. Register the plugin in TDX formula manager
echo 3. Use functions in formulas: DLLNAME@FUNCTION_MARK(parameters)
echo.
pause 