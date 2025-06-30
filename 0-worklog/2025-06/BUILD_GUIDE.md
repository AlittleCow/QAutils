# TDX Plugin Build Guide - Visual Studio 2022

## Overview
This guide covers the complete setup process for building TDX (通达信) plugins using Visual Studio 2022, including installation of all required tools and the build process.

## Prerequisites
- Windows 10/11 (64-bit)
- Administrator privileges for software installation
- Internet connection for downloads

---

## Step 1: Install Visual Studio 2022 Build Tools

### 1.1 Download Visual Studio 2022
1. Go to https://visualstudio.microsoft.com/downloads/
2. Download **Visual Studio 2022 Community** (free version)
3. Run the installer (`vs_community.exe`)

### 1.2 Select Required Workloads
During installation, select these components:

**Essential Workloads:**
- ✅ **Desktop development with C++**

**Individual Components (verify these are included):**
- ✅ **MSVC v143 - VS 2022 C++ x64/x86 build tools**
- ✅ **Windows 10/11 SDK** (latest version)
- ✅ **CMake tools for Visual Studio** (optional, for IDE integration)

### 1.3 Complete Installation
- Click "Install" and wait for completion (may take 30-60 minutes)
- Restart computer when prompted

---

## Step 2: Install CMake

### 2.1 Download CMake
1. Go to https://cmake.org/download/
2. Download **Windows x64 Installer** (cmake-3.x.x-windows-x86_64.msi)
3. Run the installer

### 2.2 Installation Options
During CMake installation:
- ✅ Check "**Add CMake to system PATH for all users**"
- Choose installation directory (default: `C:\Program Files\CMake`)
- Complete installation

### 2.3 Verify Installation
Open Command Prompt and run:
```cmd
cmake --version
```
Should display CMake version (e.g., `cmake version 3.29.0`)

---

## Step 3: Verify Visual Studio Installation

### 3.1 Find Developer Command Prompt
- **Start Menu** → Search for "**Developer Command Prompt for VS 2022**"
- Or find "**x86 Native Tools Command Prompt for VS 2022**" (for 32-bit builds)

### 3.2 Test Compiler
In Developer Command Prompt, run:
```cmd
cl
```
Should display Microsoft C/C++ compiler information

---

## Step 4: Build the TDX Plugin

### 4.1 Navigate to Project Directory
```cmd
cd C:\path\to\your\project\ChanlunX2019
```

### 4.2 Create Build Directory
```cmd
mkdir build
cd build
```

### 4.3 Configure CMake for Visual Studio 2022
```cmd
cmake -G "Visual Studio 17 2022" -A Win32 ..
```

**Expected Output:**
- Should detect Windows SDK version
- Should identify MSVC compiler
- Should configure for x86 (32-bit) architecture
- Should end with "Build files have been written to..."

### 4.4 Build the Project
```cmd
cmake --build . --config Release
```

**Expected Output:**
- Compiles all .cpp files
- Creates ChanlunX.dll in Release folder
- Shows "ChanlunX.vcxproj -> ...ChanlunX.dll"

### 4.5 Verify Build Results
```cmd
dir Release
```

**Should contain:**
- `ChanlunX.dll` (main plugin file)
- `ChanlunX.exp` (export file)
- `ChanlunX.lib` (import library)

---

## Step 5: Deploy to TDX

### 5.1 Copy Plugin File
1. Locate the built DLL: `build\Release\ChanlunX.dll`
2. Copy to TDX directory: `[TDX_Installation]\T0002\dlls\`
3. Ensure TDX is closed during copy operation

### 5.2 Configure in TDX
1. Open TDX (通达信)
2. Bind the DLL as function #2
3. Create main chart formula using the provided code

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "cmake is not recognized"
**Solution:** 
- Ensure CMake is installed with PATH option checked
- Restart Command Prompt
- Manually add `C:\Program Files\CMake\bin` to PATH

#### Issue: "cl is not recognized"
**Solution:**
- Use "Developer Command Prompt for VS 2022" instead of regular cmd
- Verify Visual Studio 2022 is properly installed

#### Issue: CMake can't find Visual Studio
**Solution:**
- Ensure Visual Studio Build Tools are installed
- Use exact generator name: "Visual Studio 17 2022"
- Verify C++ workload is installed

#### Issue: Build fails with linker errors
**Solution:**
- Ensure using Win32 architecture: `-A Win32`
- Check all source files are present
- Verify Windows SDK is installed

---

## Quick Reference Commands

### Full Build Process (from project root):
```cmd
cd ChanlunX2019
mkdir build
cd build
cmake -G "Visual Studio 17 2022" -A Win32 ..
cmake --build . --config Release
```

### Rebuild After Code Changes:
```cmd
cd ChanlunX2019\build
cmake --build . --config Release
```

### Clean Build:
```cmd
cd ChanlunX2019
rmdir /s build
mkdir build
cd build
cmake -G "Visual Studio 17 2022" -A Win32 ..
cmake --build . --config Release
```

---

## File Structure After Build

```
ChanlunX2019/
├── build/
│   ├── Release/
│   │   ├── ChanlunX.dll    ← Main plugin file
│   │   ├── ChanlunX.exp
│   │   └── ChanlunX.lib
│   ├── ChanlunX.sln        ← Visual Studio solution
│   └── ChanlunX.vcxproj    ← Visual Studio project
├── *.cpp                   ← Source files
├── *.h                     ← Header files
└── CMakeLists.txt          ← Build configuration
```

---

## Version Information

- **Visual Studio:** 2022 (v17)
- **CMake:** 3.29.0 or later
- **Target Architecture:** Win32 (32-bit)
- **Output:** Windows DLL for TDX plugin

---

## Notes

1. **32-bit Requirement:** TDX plugins must be compiled as 32-bit (Win32), hence the `-A Win32` flag
2. **Release Build:** Always use Release configuration for production plugins
3. **Path Spaces:** If project path contains spaces, use quotes in commands
4. **Antivirus:** Some antivirus software may flag the DLL during build - add exclusions if needed

---

## Support

For build issues:
1. Check Visual Studio Installer for missing components
2. Verify CMake PATH configuration
3. Ensure using Developer Command Prompt
4. Check Windows SDK installation
5. Verify project files are not corrupted

Last Updated: $(date)
Build Environment: Windows 10/11 + Visual Studio 2022 + CMake 3.29+ 