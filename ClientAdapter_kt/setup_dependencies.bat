@echo off
echo Setting up dependencies for QAUtils KT Plugin...
echo.

REM Check if vcpkg exists
if exist "..\..\vcpkg\vcpkg.exe" (
    echo vcpkg already exists and is ready
) else (
    echo Installing vcpkg...
    cd ..\..
    if exist "vcpkg" rmdir /s /q vcpkg
    echo Cloning vcpkg from mirror...
    git clone https://gitee.com/mirrors/vcpkg.git
    cd vcpkg
    call bootstrap-vcpkg.bat
    cd ..\..
)

REM Install required packages for 32-bit
echo Installing ZeroMQ for x86-windows...
..\..\vcpkg\vcpkg.exe install zeromq:x86-windows

echo Installing cppzmq for x86-windows...
..\..\vcpkg\vcpkg.exe install cppzmq:x86-windows

echo Installing nlohmann-json for x86-windows...
..\..\vcpkg\vcpkg.exe install nlohmann-json:x86-windows

echo.
echo Dependencies installation completed!
echo You can now build the 32-bit plugin with server support.
echo.
pause