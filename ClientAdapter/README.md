# QAUtils TDX Plugin Framework

## Overview

This is a modern, Object-Oriented C++ framework for creating TDX (TongDaXin) plugins. It provides a clean, extensible architecture that maintains full compatibility with the TDX plugin interface while offering the benefits of modern C++ design patterns.

## Features

- **Object-Oriented Design**: Clean separation of concerns with abstract interfaces and concrete implementations
- **Thread-Safe Registry**: Centralized function management with thread-safe operations
- **Automatic Memory Management**: RAII principles and smart pointers for safe resource management
- **Comprehensive Error Handling**: Robust error handling with detailed logging
- **Performance Monitoring**: Built-in performance timing utilities
- **Extensible Architecture**: Easy to add new functions and customize behavior
- **Full TDX Compatibility**: Maintains complete compatibility with TDX plugin interface

## Architecture

### Core Components

1. **ITdxFunction**: Abstract interface defining the contract for all TDX functions
2. **TdxFunctionBase**: Base implementation providing common functionality
3. **TdxFunctionRegistry**: Singleton registry for managing all functions
4. **TdxPluginManager**: Main plugin lifecycle management
5. **TdxUtilities**: Utility functions for common operations

### Class Hierarchy

```
ITdxFunction (abstract interface)
├── TdxFunctionBase (base implementation)
    ├── SequenceFunction
    ├── AverageFunction
    ├── SimpleMovingAverageFunction
    └── ExponentialMovingAverageFunction
```

## Quick Start

### Building the Plugin

1. **Prerequisites**:
   - CMake 3.10 or higher
   - Visual Studio 2017 or higher (Windows)
   - C++17 compatible compiler


# use vcpkg on windows to install 3rd party libs
git clone https://github.com/microsoft/vcpkg.git

 .\vcpkg install nlohmann-json:x86-windows
 .\vcpkg.exe install zeromq:x86-windows
 .\vcpkg.exe install cppzmq:x86-windows

2. **Build Steps**:
   ```bash
   mkdir build
   cd build
   cmake ..
   cmake --build . --config Release
   ```

3. **Output**: `QAUtilsTdxPlugin.dll` will be created in the `bin` directory

### Using with TDX

1. Copy the generated DLL to your TDX installation directory
2. Register the plugin in TDX formula manager
3. Use functions in formulas: `DLLNAME@FUNCTION_MARK(parameters)`

## Creating Custom Functions

### Step 1: Define Your Function Class

```cpp
class MyCustomFunction : public TdxFunctionBase
{
public:
    MyCustomFunction() 
        : TdxFunctionBase(100, "MyCustomFunction", "Description of my function")
    {
    }

protected:
    bool CalculateCore(int nCount, float* pOut, const float* pInA,
                      const float* pInB, const float* pInC) override
    {
        // Your calculation logic here
        for (int i = 0; i < nCount; ++i)
        {
            pOut[i] = /* your calculation */;
        }
        return true;
    }
};
```

### Step 2: Register Your Function

```cpp
// In TdxPluginManager::RegisterBuiltInFunctions()
auto& registry = TdxFunctionRegistry::GetInstance();
registry.RegisterFunction(std::make_shared<MyCustomFunction>());
```

### Step 3: Use in TDX

```
// In TDX formula
MY_RESULT: DLLNAME@100();
```

## Built-in Functions

### Function 1: SequenceFunction
- **Mark**: 1
- **Description**: Generates sequential values (0, 1, 2, 3, ...)
- **Usage**: `SEQUENCE: DLLNAME@1();`

### Function 2: AverageFunction
- **Mark**: 2
- **Description**: Calculates average of three input arrays
- **Usage**: `AVG: DLLNAME@2(CLOSE, OPEN, HIGH);`

### Function 3: SimpleMovingAverageFunction
- **Mark**: 3
- **Description**: Calculates Simple Moving Average
- **Usage**: `SMA: DLLNAME@3(CLOSE, 5);`

### Function 4: ExponentialMovingAverageFunction
- **Mark**: 4
- **Description**: Calculates Exponential Moving Average
- **Usage**: `EMA: DLLNAME@4(CLOSE, 12);`

## Advanced Features

### Performance Monitoring

```cpp
void MyFunction::SomeMethod()
{
    TDX_MEASURE_PERFORMANCE("MyFunction::SomeMethod");
    
    // Your code here
    // Performance will be automatically measured and logged
}
```

### Custom Validation

```cpp
bool MyFunction::ValidateInputs(int nCount, const float* pOut, 
                               const float* pInA, const float* pInB, 
                               const float* pInC) const override
{
    // Call base validation
    if (!TdxFunctionBase::ValidateInputs(nCount, pOut, pInA, pInB, pInC))
        return false;
    
    // Your custom validation logic
    if (pInA == nullptr)
    {
        LogError("Input A is required");
        return false;
    }
    
    return true;
}
```

### Error Handling and Logging

```cpp
void MyFunction::SomeMethod()
{
    try
    {
        // Your code here
        LogDebug("Debug message");
    }
    catch (const std::exception& e)
    {
        LogError("Error occurred: " + std::string(e.what()));
    }
}
```

## Utility Functions

### Array Operations

```cpp
// Validate array
if (!TdxUtilities::ValidateArray(pArray, nSize, "MyArray"))
    return false;

// Fill array with value
TdxUtilities::FillArray(pOut, nCount, 0.0f);

// Calculate statistics
float mean = TdxUtilities::MeanArray(pArray, nSize);
float min = TdxUtilities::MinArray(pArray, nSize);
float max = TdxUtilities::MaxArray(pArray, nSize);
```

### Safe Operations

```cpp
// Safe division
float result = TdxUtilities::SafeDivide(numerator, denominator, 0.0f);

// Value clamping
float clamped = TdxUtilities::ClampValue(value, 0.0f, 100.0f);

// Linear interpolation
float interpolated = TdxUtilities::LinearInterpolate(value1, value2, 0.5f);
```

## Configuration

### Build Options

- `BUILD_TESTS`: Enable test programs (default: OFF)
- `CMAKE_BUILD_TYPE`: Debug/Release/RelWithDebInfo/MinSizeRel

### Preprocessor Definitions

- `TDXPLUGIN_EXPORTS`: Export symbols for DLL
- `_DEBUG`: Enable debug logging
- `WIN32_LEAN_AND_MEAN`: Minimize Windows headers

## Troubleshooting

### Common Issues

1. **DLL not loading**: Ensure all dependencies are available
2. **Function not found**: Check function mark numbers are unique
3. **Crashes**: Verify array bounds and null pointer checks
4. **Performance issues**: Use performance monitoring to identify bottlenecks

### Debug Output

Enable debug logging by building in Debug configuration:
```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
```

### Error Codes

- Registry errors are logged to console and Windows debug output
- Function validation errors include detailed parameter information
- Performance timing is automatically logged for all functions

## Contributing

1. Follow the existing code style and patterns
2. Add comprehensive documentation for new functions
3. Include input validation and error handling
4. Add performance monitoring where appropriate
5. Test thoroughly with various input scenarios

## License

This framework is provided as-is for educational and development purposes. Please ensure compliance with TDX plugin development guidelines and licensing requirements.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the example functions for patterns
- Examine the debug output for detailed error information

---

*Generated by QAUtils TDX Plugin Framework v1.0.0* 