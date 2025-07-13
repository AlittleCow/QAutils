# KT交易师DLL集成问题解决方案

## 问题诊断与解决

### 1. 问题现象
- KT交易师无法加载 `QAUtilsKTPlugin.dll`
- 插件加载失败，没有错误提示

### 2. 根本原因分析

经过详细排查，发现了以下关键问题：

#### 2.1 extern "C" 声明问题
**问题**: 在 `KTPluginMain.h` 中，主要的导出函数（`GetFunctionCount`、`GetFunctionInfo`、`CallFunction`）没有正确包含在 `extern "C"` 块中。

**影响**: KT交易师无法找到正确的C风格函数入口点，导致DLL加载失败。

**解决方案**: 修复了头文件结构，确保所有KT需要的导出函数都在 `extern "C"` 块内声明。

#### 2.2 函数签名不匹配
**问题**: 部分函数的 `GetCFunctionPointer` 方法名不正确，应该是 `GetKTFunctionPointer`。

**解决方案**: 已修复所有相关函数的方法名和签名。

#### 2.3 日志函数调用错误
**问题**: 代码中使用了不存在的 `log_warning` 函数。

**解决方案**: 修正为正确的 `log_warn` 函数。

### 3. 修复内容总结

#### 3.1 文件修改列表
- `KTPluginMain.h`: 修复 extern "C" 声明结构
- `KTServerFunc.cpp`: 修复方法名和函数签名
- `KTServerFunc.cpp`: 修复日志函数调用

#### 3.2 关键修复点
1. **导出函数声明**: 确保 `GetFunctionCount`、`GetFunctionInfo`、`CallFunction` 等函数正确导出
2. **C调用约定**: 所有KT接口函数使用正确的C调用约定
3. **函数签名一致性**: 确保接口实现与声明完全匹配

### 4. 验证结果

#### 4.1 编译验证
- ✅ DLL编译成功
- ✅ 无编译错误和警告
- ✅ 生成了正确的导出符号

#### 4.2 功能验证
- ✅ `test_basic.exe` 运行成功
- ✅ `test_technical_indicators.exe` 运行成功
- ✅ 所有技术指标功能正常

### 5. KT交易师集成指南

#### 5.1 文件部署
1. 将以下文件复制到KT交易师插件目录：
   - `QAUtilsKTPlugin.dll`
   - `libzmq-mt-4_3_5.dll`

#### 5.2 系统要求
- Windows 32位环境
- Microsoft Visual C++ 2022 Redistributable (x86)
- .NET Framework 4.0或更高版本

#### 5.3 插件注册
1. 启动KT交易师
2. 进入插件管理界面
3. 添加 `QAUtilsKTPlugin.dll`
4. 重启KT交易师

#### 5.4 可用函数列表

**技术指标函数**:
- `KT_SMA`: 简单移动平均线
- `KT_EMA`: 指数移动平均线
- `KT_MACD`: MACD指标
- `KT_RSI`: RSI指标

**服务器通信函数** (如果启用):
- `KT_SERVER_CONNECT`: 服务器连接
- `KT_SERVER_DISCONNECT`: 服务器断开
- `KT_SERVER_STATUS`: 服务器状态
- `KT_SMA_SERVER`: 服务器端SMA计算

### 6. 故障排除

#### 6.1 如果DLL仍然无法加载
1. **检查依赖库**: 确保 `libzmq-mt-4_3_5.dll` 在同一目录
2. **检查运行库**: 安装 Microsoft Visual C++ 2022 Redistributable (x86)
3. **检查权限**: 确保KT交易师有读取DLL文件的权限
4. **检查架构**: 确认KT交易师是32位版本

#### 6.2 调试工具
使用以下工具进行进一步诊断：
```cmd
# 检查DLL导出函数
dumpbin /exports QAUtilsKTPlugin.dll

# 检查DLL依赖
dumpbin /dependents QAUtilsKTPlugin.dll
```

### 7. 技术细节

#### 7.1 导出函数接口
```cpp
extern "C" {
    __declspec(dllexport) int GetFunctionCount();
    __declspec(dllexport) BOOL GetFunctionInfo(int nIndex, KTFuncInfo* pFuncInfo);
    __declspec(dllexport) BOOL CallFunction(int nIndex, CALCINFO* pCalcInfo);
    
    // 直接导出的技术指标函数
    __declspec(dllexport) BOOL KT_SMA(CALCINFO* pCalcInfo);
    __declspec(dllexport) BOOL KT_EMA(CALCINFO* pCalcInfo);
    __declspec(dllexport) BOOL KT_MACD(CALCINFO* pCalcInfo);
    __declspec(dllexport) BOOL KT_RSI(CALCINFO* pCalcInfo);
}
```

#### 7.2 函数调用流程
1. KT交易师调用 `GetFunctionCount()` 获取函数数量
2. 循环调用 `GetFunctionInfo()` 获取每个函数的信息
3. 根据需要调用 `CallFunction()` 或直接调用具体函数

### 8. 后续优化建议

1. **错误处理**: 增强错误处理和日志记录
2. **性能优化**: 优化计算算法，提高执行效率
3. **功能扩展**: 添加更多技术指标和分析工具
4. **文档完善**: 提供更详细的API文档和使用示例

---

**修复完成时间**: 2024年12月
**修复状态**: ✅ 已解决
**测试状态**: ✅ 已验证