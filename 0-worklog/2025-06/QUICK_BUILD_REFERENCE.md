# TDX Plugin - Quick Build Reference Card

## 🚀 Essential Setup (One-time)

### Install Visual Studio 2022
```
Download: https://visualstudio.microsoft.com/downloads/
Select: "Desktop development with C++" workload
```

### Install CMake
```
Download: https://cmake.org/download/
✅ Check "Add CMake to system PATH"
```

---

## 🔨 Build Commands

### First Build
```cmd
cd ChanlunX2019
mkdir build
cd build
cmake -G "Visual Studio 17 2022" -A Win32 ..
cmake --build . --config Release
```

### Rebuild After Changes
```cmd
cd ChanlunX2019\build
cmake --build . --config Release
```

### Clean Rebuild
```cmd
cd ChanlunX2019
rmdir /s build
mkdir build
cd build
cmake -G "Visual Studio 17 2022" -A Win32 ..
cmake --build . --config Release
```

---

## 📁 Output Location
```
ChanlunX2019\build\Release\ChanlunX.dll
```

## 🎯 Deploy to TDX
```
Copy: ChanlunX.dll → [TDX_Install]\T0002\dlls\
Bind: As function #2 in TDX
```

---

## ⚠️ Important Notes
- **Always use:** Developer Command Prompt for VS 2022
- **Architecture:** Must be Win32 (32-bit) for TDX
- **Configuration:** Always Release for production
- **Generator:** "Visual Studio 17 2022" (exact spelling)

---

## 🔧 Quick Troubleshooting
| Problem | Solution |
|---------|----------|
| `cmake not recognized` | Add `C:\Program Files\CMake\bin` to PATH |
| `cl not recognized` | Use Developer Command Prompt for VS 2022 |
| CMake can't find VS | Install "Desktop development with C++" |
| Build fails | Check `-A Win32` flag is used |

---

## 📋 Verification Checklist
- [ ] Visual Studio 2022 with C++ workload installed
- [ ] CMake in PATH (`cmake --version` works)
- [ ] Using Developer Command Prompt
- [ ] Project builds without errors
- [ ] ChanlunX.dll created in Release folder
- [ ] DLL copied to TDX dlls directory 