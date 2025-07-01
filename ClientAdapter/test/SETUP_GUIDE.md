# ZmqClient Setup Guide for Windows

This guide will help you set up the ZmqClient to work with the Python QuantServer on Windows.

## Current Status

The ZmqClient code has been created but requires dependencies to function. Without the dependencies, it will show helpful error messages and instructions.

## Option 1: Quick Test (No Dependencies Required)

You can test the current implementation to see what's missing:

### Using any C++ compiler:
```cmd
# If you have any C++ compiler (like MinGW, MSVC, or Clang)
g++ -std=c++17 ServerApi.cpp simple_test.cpp -o simple_test.exe
# or with MSVC
cl /std:c++17 ServerApi.cpp simple_test.cpp /Fe:simple_test.exe

# Run the test
simple_test.exe
```

This will show you the current dependency status and what needs to be installed.

## Option 2: Full Setup with Dependencies

### Step 1: Install a C++ Compiler

Choose one of the following:

#### Option A: Visual Studio (Recommended for Windows)
1. Download Visual Studio Community (free) from https://visualstudio.microsoft.com/
2. During installation, select "Desktop development with C++"
3. This includes the MSVC compiler and CMake

#### Option B: MinGW-w64
1. Download from https://www.mingw-w64.org/
2. Add the bin directory to your PATH
3. Install CMake separately from https://cmake.org/

### Step 2: Install vcpkg (Package Manager)

vcpkg is the easiest way to install C++ libraries on Windows:

```cmd
# Clone vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg

# Bootstrap vcpkg
.\bootstrap-vcpkg.bat

# Integrate with Visual Studio (optional but recommended)
.\vcpkg integrate install
```

### Step 3: Install Required Libraries

```cmd
# Install ZeroMQ C++ bindings
.\vcpkg install cppzmq:x64-windows

# Install nlohmann/json
.\vcpkg install nlohmann-json:x64-windows

# For 32-bit, use x86-windows instead of x64-windows
```

### Step 4: Build the Project

#### Using CMake (Recommended):
```cmd
cd QAutils/ClientAdapter/module
mkdir build
cd build

# Configure with vcpkg
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake -DZMQ_AVAILABLE=ON -DJSON_AVAILABLE=ON

# Build
cmake --build . --config Release
```

#### Manual Compilation:
```cmd
# With vcpkg installed libraries
g++ -std=c++17 -DZMQ_AVAILABLE -DJSON_AVAILABLE ^
    -I"C:/path/to/vcpkg/installed/x64-windows/include" ^
    ServerApi.cpp simple_test.cpp ^
    -L"C:/path/to/vcpkg/installed/x64-windows/lib" ^
    -lzmq -o simple_test.exe
```

## Option 3: Using Windows Subsystem for Linux (WSL)

If you prefer Linux-style development:

### Step 1: Install WSL
```cmd
wsl --install
```

### Step 2: Install dependencies in WSL
```bash
# Update package list
sudo apt update

# Install build tools
sudo apt install build-essential cmake

# Install ZeroMQ
sudo apt install libzmq3-dev libcppzmq-dev

# Install nlohmann/json
sudo apt install nlohmann-json3-dev
```

### Step 3: Build in WSL
```bash
cd /mnt/c/path/to/your/project/QAutils/ClientAdapter/module

# Compile
g++ -std=c++17 -DZMQ_AVAILABLE -DJSON_AVAILABLE \
    ServerApi.cpp simple_test.cpp \
    -lzmq -o simple_test

# Run
./simple_test
```

## Testing the Setup

### Step 1: Start the Python QuantServer
```cmd
cd QAutils/Server
python QuantServer.py
```

### Step 2: Run the C++ Client
```cmd
# In another terminal
cd QAutils/ClientAdapter/module
simple_test.exe
```

If everything is set up correctly, you should see:
- "Dependencies available: YES"
- Successful connection to the server
- Heartbeat and server info responses

## Troubleshooting

### Common Issues:

#### 1. "Dependencies available: NO"
- Make sure you compiled with `-DZMQ_AVAILABLE -DJSON_AVAILABLE` flags
- Verify libraries are installed and linked correctly

#### 2. "Failed to connect to server"
- Make sure the Python QuantServer is running
- Check the server is listening on localhost:5555
- Verify firewall settings

#### 3. Compilation Errors
- Check that all include paths are correct
- Verify library paths and linking
- Make sure C++17 standard is enabled

#### 4. "cmake not found"
- Install CMake from https://cmake.org/
- Add CMake to your system PATH

### Getting Help:

1. **Check dependency status**: Run `simple_test.exe` to see what's missing
2. **Verify installation**: Make sure vcpkg shows the libraries as installed
3. **Check paths**: Ensure all include and library paths are correct
4. **Test Python server**: Make sure the QuantServer runs independently

## Alternative Approaches

If you're having trouble with the C++ setup, consider:

1. **Use the Python client**: The `example_client.py` already works
2. **Create a Python wrapper**: Use Python's subprocess to call C++ code
3. **Use a simpler HTTP-based API**: Consider creating a REST API instead of ZMQ

## Next Steps

Once you have the basic setup working:

1. Test all the API functions (SMA, RSI, Bollinger Bands, etc.)
2. Add error handling for your specific use cases
3. Integrate with your existing C++ codebase
4. Consider creating a static library for easier distribution

## Files Overview

- `ServerApi.h` - Header file with class declaration
- `ServerApi.cpp` - Implementation with dependency checking
- `simple_test.cpp` - Basic test program
- `example_usage.cpp` - Full example with all features
- `CMakeLists.txt` - Build configuration
- `SETUP_GUIDE.md` - This guide

The implementation is designed to be helpful even when dependencies are missing, providing clear instructions on what needs to be installed. 