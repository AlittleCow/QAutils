@echo off
echo Building QAUtils KT Plugin (32-bit with Server Support)...
echo.

REM Set vcpkg toolchain
set VCPKG_ROOT=..\..\vcpkg
set CMAKE_TOOLCHAIN_FILE=%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake
set VCPKG_TARGET_TRIPLET=x86-windows

REM Create build directory
if exist build32_server rmdir /s /q build32_server
mkdir build32_server
cd build32_server

echo Configuring CMake for 32-bit with server support...
cmake .. -G "Visual Studio 17 2022" -A Win32 -DCMAKE_TOOLCHAIN_FILE=%CMAKE_TOOLCHAIN_FILE% -DVCPKG_TARGET_TRIPLET=%VCPKG_TARGET_TRIPLET%

if %ERRORLEVEL% neq 0 (
    echo CMake configuration failed!
    pause
    exit /b 1
)

echo Building Debug version...
cmake --build . --config Debug

if %ERRORLEVEL% neq 0 (
    echo Debug build failed!
    pause
    exit /b 1
)

echo Building Release version...
cmake --build . --config Release

if %ERRORLEVEL% neq 0 (
    echo Release build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Debug DLL: build32_server\bin\Debug\QAUtilsKTPlugin.dll
echo Release DLL: build32_server\bin\Release\QAUtilsKTPlugin.dll
echo.
echo The plugin now includes server communication features.
echo Make sure the Python server is running before using server functions.
echo.
pause