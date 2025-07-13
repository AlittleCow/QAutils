# QAUtils KT Plugin

一个为KT交易师（金字塔决策交易系统）设计的高性能C++插件，提供完整的技术分析功能和可选的服务器通信能力。

## 🚀 项目概述

QAUtils KT Plugin是一个专业的交易分析插件，专为KT交易师平台开发。插件采用现代化的模块化设计，提供两种调用方式：**直接函数调用**（推荐）和**框架调用**，支持基础技术分析功能，并可选择性地启用服务器通信功能。

## ✨ 最新更新

- ✅ **直接函数导出**：新增 `KT_SMA`、`KT_EMA`、`KT_RSI`、`KT_MACD` 直接导出函数
- ✅ **双重调用机制**：支持直接调用和框架调用两种方式
- ✅ **完整测试验证**：所有技术指标测试通过
- ✅ **详细使用文档**：提供完整的安装和使用指南
- ✅ **自动初始化**：插件自动处理初始化和清理工作

## 🎯 主要特性

### 📊 技术指标函数
- **SMA（简单移动平均线）**：`KT_SMA` - 支持任意周期
- **EMA（指数移动平均线）**：`KT_EMA` - 支持任意周期
- **RSI（相对强弱指标）**：`KT_RSI` - 经典超买超卖指标
- **MACD指标**：`KT_MACD` - 包含MACD线、信号线、柱状图

### 🔧 核心功能
- **双重调用机制**：直接函数调用 + 框架调用
- **自动初始化**：插件自动处理生命周期管理
- **函数注册系统**：动态函数注册和管理
- **完整日志系统**：详细的调试和运行时日志支持
- **CALCINFO接口**：与KT平台的标准数据交换
- **线程安全**：支持多线程环境下的安全调用

### 🌐 可选功能（需要依赖）
- **服务器通信**：基于ZeroMQ的实时数据传输
- **JSON数据处理**：使用nlohmann/json进行数据序列化
- **实时数据推送**：K线数据、技术指标结果推送

## 项目结构

```
ClientAdapter_kt/
├── core/                    # 核心框架
│   ├── IKTFunction.h       # 函数接口定义
│   ├── KTFunctionBase.*    # 函数基类
│   ├── KTFunctionRegistry.*# 函数注册管理
│   └── KTPluginMain.*      # 插件主入口
├── module/                  # 功能模块
│   ├── KTCommonFunc.*      # 通用函数实现
│   ├── KTServerFunc.*      # 服务器功能（可选）
│   └── KTServerApi.*       # 服务器API（可选）
├── utils/                   # 工具类
│   └── log.*               # 日志系统
├── test/                    # 测试程序
│   ├── test_basic.cpp      # 基础功能测试
│   ├── test_technical_indicators.cpp # 技术指标测试
│   └── test_direct_exports.cpp # 直接导出函数测试
├── build_scripts/           # 构建脚本
├── setup_dependencies.bat  # 依赖安装脚本
├── build_32bit_with_server.bat # 32位构建脚本
└── CMakeLists.txt          # CMake配置
```

## 构建要求

### 必需依赖
- **Visual Studio 2019/2022**（MSVC编译器）
- **CMake 3.15+**
- **Windows SDK**

### 可选依赖（服务器功能）
- **vcpkg**（包管理器）
- **ZeroMQ**（消息队列）
- **cppzmq**（ZeroMQ C++绑定）
- **nlohmann-json**（JSON处理）

## 快速开始

# QAUtils ClientAdapter KT

一个为 KT交易师 设计的高性能技术指标计算插件。

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)]()
[![Language](https://img.shields.io/badge/language-C++-blue)]()

## 🚀 功能特性

- **📊 技术指标计算**: SMA, EMA, MACD, RSI 等常用技术指标
- **🌐 服务器通信**: 支持远程数据获取和实时计算
- **⚡ 高性能**: 优化的 C++ 实现，适合实时交易环境
- **🔌 易于集成**: 标准的 KT 插件接口，即插即用
- **🛡️ 稳定可靠**: 完整的错误处理和日志系统
- **📚 文档完善**: 详细的使用指南和示例代码

## 📦 快速开始

### 系统要求
- Windows 10/11 (32位或64位)
- KT交易师软件
- Microsoft Visual C++ 2022 Redistributable (x86)
- CMake 3.20+
- Visual Studio 2019/2022

### 完整安装和使用流程

#### 1. 获取依赖
```bash
# 运行依赖安装脚本
setup_dependencies.bat
```

#### 2. 编译项目
```bash
# 编译32位版本（KT交易师要求）
build_32bit_with_server.bat
```

#### 3. 部署插件
- 找到编译生成的 `QAUtilsKTPlugin.dll` 文件
- 将 `QAUtilsKTPlugin.dll` 和 `libzmq-mt-4_3_5.dll` 复制到 KT交易师安装目录下的 `kt\fmldll` 文件夹中

#### 4. 在KT交易师中测试
启动KT交易师，在公式编辑器中输入以下代码进行测试：

```
EMA12 := "QAUtilsKTPlugin@KT_EMA";
EMA26 := "QAUtilsKTPlugin@KT_EMA2";
RSI14 := "QAUtilsKTPlugin@KT_RSI";
MACD := "QAUtilsKTPlugin@KT_MACD";

// 绘图展示（副图）
PLOT1 := EMA12;
PLOT2 := EMA26;
PLOT3 := RSI14;
PLOT4 := MACD;
```

详细安装说明请参考 [快速开始指南](QUICKSTART.md)

## 🛠️ 开发构建

### 编译环境
- Visual Studio 2019/2022
- CMake 3.15+
- vcpkg (依赖管理)

### 编译步骤
```bash
# 克隆仓库
git clone https://github.com/你的用户名/QAUtils-ClientAdapter-KT.git
cd QAUtils-ClientAdapter-KT

# 创建构建目录
mkdir build
cd build

# 配置项目 (32位)
cmake .. -A Win32 -DCMAKE_TOOLCHAIN_FILE=path/to/vcpkg/scripts/buildsystems/vcpkg.cmake

# 编译
cmake --build . --config Release
```

## 📋 功能模块

### 技术指标
| 指标 | 函数名 | 描述 |
|------|--------|------|
| SMA | `KT_SMA` | 简单移动平均线 |
| EMA | `KT_EMA` | 指数移动平均线 |
| MACD | `KT_MACD` | 移动平均收敛散度 |
| RSI | `KT_RSI` | 相对强弱指标 |

### 服务器功能 (可选)
- 远程连接管理
- 实时数据同步
- 服务器端计算
- 状态监控

## 🧪 测试验证

```bash
# 运行基础功能测试
.\build\bin\Release\test_basic.exe

# 运行技术指标测试
.\build\bin\Release\test_technical_indicators.exe

# 验证DLL导出
.\verify_dll.bat
```

## 📖 文档资源

- [📘 使用指南](USAGE.md) - 详细的功能说明和配置
- [🚀 快速开始](QUICKSTART.md) - 快速上手指南
- [🔧 集成解决方案](KT_INTEGRATION_SOLUTION.md) - 问题排查和解决
- [📤 GitHub上传指南](GITHUB_UPLOAD_GUIDE.md) - 项目上传说明
- [📝 公式示例](kt_formula_examples.txt) - KT公式使用示例

## 🐛 故障排除

### 常见问题

**Q: DLL加载失败**
- 检查依赖库是否完整
- 确认Visual C++运行库已安装
- 验证KT交易师版本兼容性

**Q: 函数调用错误**
- 检查参数格式和数量
- 查看日志文件获取详细错误信息
- 参考示例代码和文档

更多问题解决方案请查看 [集成解决方案文档](KT_INTEGRATION_SOLUTION.md)

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发规范
- 遵循现有代码风格
- 添加适当的注释和文档
- 确保所有测试通过
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 📞 支持与反馈

- 🐛 **Bug报告**: [创建Issue](../../issues/new?template=bug_report.md)
- 💡 **功能建议**: [创建Issue](../../issues/new?template=feature_request.md)
- 📧 **技术支持**: 通过Issue或邮件联系
- 💬 **讨论交流**: [Discussions](../../discussions)

## 🏆 致谢

感谢所有为本项目做出贡献的开发者和用户！

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！

### 当前状态

✅ **编译完成**: 插件已成功编译在 `build32` 目录  
✅ **测试通过**: 所有技术指标测试已通过  
❌ **服务器功能**: 当前未启用（可选功能）  
📍 **插件位置**: `build32\bin\Release\QAUtilsKTPlugin.dll`

### 1. 克隆项目
```bash
git clone <repository-url>
cd ClientAdapter_kt
```

### 2. 安装依赖（可选）
```bash
# 自动安装vcpkg和相关依赖
.\setup_dependencies.bat
```

### 3. 构建插件
```bash
# 构建32位版本（推荐）
.\build_32bit_with_server.bat

# 或使用CMake手动构建
mkdir build && cd build
cmake .. -A Win32
cmake --build . --config Release
```

### 4. 测试插件
```bash
# 运行基础功能测试
.\build32_server\bin\Debug\test_basic.exe

# 运行技术指标测试
.\build32_server\bin\Debug\test_technical_indicators.exe
```

## 构建配置

### 条件编译
插件支持条件编译，可以根据依赖的可用性自动调整功能：

- **ENABLE_SERVER_FUNCTIONS**：当找到ZeroMQ、cppzmq和nlohmann-json时自动启用
- 如果依赖不完整，插件将以基础模式编译，仍可提供核心功能

### 构建目标

**当前可用的构建版本**:

```bash
# 基础版本（仅本地函数）- 已编译完成 ✅
cmake --build build32 --config Release
# 输出: build32\bin\Release\QAUtilsKTPlugin.dll

# 服务器版本（包含网络功能）- 需要依赖库
cmake --build build32_server --config Release
# 需要先安装: ZeroMQ, cppzmq, nlohmann-json
```

**快速使用当前版本**:
```bash
# 直接使用已编译的插件
cp build32\bin\Release\QAUtilsKTPlugin.dll "KT交易师安装目录\Plugins\"
```

**构建输出文件**:
- **QAUtilsKTPlugin.dll**：主插件DLL
- **test_basic.exe**：基础功能测试程序
- **test_technical_indicators.exe**：技术指标测试程序

## 💻 使用方法

### 📦 插件安装
1. 将编译好的 `QAUtilsKTPlugin.dll` 复制到KT交易师的插件目录
2. 在KT交易师中加载插件（系统设置 → 插件管理 → 添加插件）
3. 确认插件加载成功

### 🎯 在KT公式中调用（推荐方式）

### 当前可用功能

**✅ 本地技术指标函数**（已测试通过）:

#### 直接函数调用
```pascal
// 计算20周期简单移动平均线
SMA20 := CALLDLL('QAUtilsKTPlugin.dll', 'KT_SMA', 20);

// 计算12周期指数移动平均线
EMA12 := CALLDLL('QAUtilsKTPlugin.dll', 'KT_EMA', 12);

// 计算14周期RSI
RSI14 := CALLDLL('QAUtilsKTPlugin.dll', 'KT_RSI', 14);

// 计算MACD(12,26,9)
MACD_LINE := CALLDLL('QAUtilsKTPlugin.dll', 'KT_MACD', 12, 26, 9, 0); // MACD线
SIGNAL_LINE := CALLDLL('QAUtilsKTPlugin.dll', 'KT_MACD', 12, 26, 9, 1); // 信号线
HISTOGRAM := CALLDLL('QAUtilsKTPlugin.dll', 'KT_MACD', 12, 26, 9, 2); // 柱状图
```

**❌ 服务器功能**（需要启用）:
```pascal
// 需要先启用服务器功能
// 参考 SERVER_SETUP.md 进行配置
// SERVER_SMA := CALLDLL('QAUtilsKTPlugin.dll', 'KT_SERVER_CALL_API', "sma", 20);
```

#### 框架调用（兼容模式）
```pascal
// 使用函数ID调用
SMA20 := CALLDLL('QAUtilsKTPlugin.dll', 'CallFunction', 2001, 20); // 2001是SMA的函数ID
```

### 📈 实际策略示例

#### 双均线策略
```pascal
SMA_SHORT := CALLDLL('QAUtilsKTPlugin.dll', 'KT_SMA', 5);
SMA_LONG := CALLDLL('QAUtilsKTPlugin.dll', 'KT_SMA', 20);

// 金叉买入信号
BUY_SIGNAL := (SMA_SHORT > SMA_LONG) AND (REF(SMA_SHORT, 1) <= REF(SMA_LONG, 1));
```

#### RSI超买超卖策略
```pascal
RSI14 := CALLDLL('QAUtilsKTPlugin.dll', 'KT_RSI', 14);

// 超卖买入信号（RSI < 30）
OVERSOLD := RSI14 < 30;
// 超买卖出信号（RSI > 70）
OVERBOUGHT := RSI14 > 70;
```

### 🌐 服务器功能（可选）
如需使用服务器功能，请参考 `SERVER_SETUP.md` 文档。

## 📚 详细文档

- **[安装使用指南](KT_PLUGIN_INSTALLATION_GUIDE.md)**：完整的插件安装和使用说明
- **[公式使用手册](KT_FORMULA_USAGE.md)**：详细的KT公式调用方法和示例
- **[服务器配置](SERVER_SETUP.md)**：服务器功能的配置和使用（可选）

## 🛠️ 开发指南

### 添加新的技术指标
1. 在 `module/KTCommonFunc.cpp` 中实现函数类
2. 在 `RegisterKTCommonFunctions()` 中注册函数
3. 在 `core/KTPluginMain.cpp` 中添加直接导出函数
4. 在 `core/KTPluginMain.h` 中添加函数声明
5. 添加相应的测试用例

### 添加服务器功能
1. 在 `module/KTServerFunc.cpp` 中实现
2. 使用 `#ifdef ENABLE_SERVER_FUNCTIONS` 保护代码
3. 在 `RegisterKTServerFunctions()` 中注册

### 日志使用
```cpp
#include "utils/log.h"

log_info("信息日志");
log_warn("警告日志");
log_error("错误日志");
```

### 性能优化建议
- 优先使用直接函数调用，性能更好
- 合理设置技术指标的周期参数
- 在复杂策略中缓存计算结果，避免重复计算

## 故障排除

### 常见问题

**Q: 编译时找不到ZeroMQ**
A: 运行`setup_dependencies.bat`安装依赖，或禁用服务器功能进行基础编译

**Q: 插件在KT平台中无法加载**
A: 确保使用32位编译，检查依赖DLL是否在PATH中

**Q: 测试程序运行失败**
A: 检查工作目录是否正确，确保在项目根目录运行

### 调试模式
- Debug版本包含完整的调试信息和日志输出
- 使用Visual Studio附加到KT进程进行调试
- 查看日志文件了解运行时问题

## 📋 版本历史

### v1.3.0 (当前版本) - 2024年12月
- ✅ **核心功能**: SMA, EMA, RSI, MACD 技术指标
- ✅ **编译状态**: build32目录编译完成
- ✅ **测试验证**: 所有技术指标测试通过
- ✅ **双重调用**: 直接导出函数 + 框架调用
- ✅ **错误处理**: 完整的日志系统和错误检查
- ✅ **自动初始化**: 首次调用自动初始化框架
- ❌ **服务器功能**: 未启用（需要安装依赖）
- 📁 **文件位置**: `build32\bin\Release\QAUtilsKTPlugin.dll`

### 历史版本
- **v1.0.0**：初始版本，基础技术分析功能
- **v1.1.0**：添加服务器通信功能
- **v1.2.0**：优化构建系统，支持条件编译
- **v1.3.0**：🆕 添加直接函数导出，支持双重调用机制
  - 新增 `KT_SMA`、`KT_EMA`、`KT_RSI`、`KT_MACD` 直接导出函数
  - 完善错误处理和自动初始化
  - 添加完整的使用文档和测试验证
  - 优化性能和内存管理

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件
- 项目讨论区

---

**注意**：本插件专为KT交易平台设计，使用前请确保了解相关的交易风险和合规要求。