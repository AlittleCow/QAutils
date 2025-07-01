# TDX Server API Integration with ZeroMQ QuantServer

## Overview

This document describes the integration between TDX plugin functions and the ZeroMQ-based QuantServer for real-time financial data processing and technical indicator calculations.

## Architecture

### Components
1. **TdxServerFunc.cpp/h** - TDX plugin functions that interface with ZeroMQ client
2. **ServerApi.h/cpp** - ZeroMQ client wrapper for C++ integration
3. **QuantServer.py** - Python ZeroMQ server handling calculations
4. **ServerManager** - Singleton managing server connections and state

### Communication Flow
```
TDX Plugin → ZmqClient → ZeroMQ → QuantServer (Python) → Response → TDX Plugin
```

## Server Functions

### Core Server Operations

#### TDXSERVER_HEARTBEAT (ID: 10)
- **Purpose**: Test server connectivity and measure response time
- **Parameters**: 
  - pInA: Client timestamp
  - pOut: Server response time or error code
- **ZeroMQ Integration**: Uses `testHeartbeat()` method
- **Fallback**: Local timestamp simulation if server unavailable

#### TDXSERVER_GETINFO (ID: 11)
- **Purpose**: Retrieve server information and status
- **Parameters**:
  - pInA: Info type (0=status, 1=version, 2=uptime, 3=connections)
  - pOut: Requested information value
- **ZeroMQ Integration**: Uses `getServerInfo()` method
- **Fallback**: Local ServerManager data

#### TDXSERVER_CONNECT (ID: 12)
- **Purpose**: Establish client connection with server
- **Parameters**:
  - pInA: Client ID
  - pInB: Connection timeout
  - pOut: Connection result
- **ZeroMQ Integration**: Attempts server reconnection if needed

#### TDXSERVER_DISCONNECT (ID: 13)
- **Purpose**: Disconnect client from server
- **Parameters**:
  - pInA: Client ID
  - pOut: Disconnection result

### Data Validation and Statistics

#### TDXSERVER_VALIDATEDATA (ID: 14)
- **Purpose**: Validate data integrity
- **Parameters**:
  - pInA: Data to validate
  - pInB: Expected checksum
  - pInC: Validation type (0=sum, 1=square, 2=absolute)
  - pOut: Validation result (1=valid, 0=invalid)

#### TDXSERVER_GETSTATS (ID: 15)
- **Purpose**: Get server performance statistics
- **Parameters**:
  - pInA: Stat type (0=memory, 1=CPU, 2=network, 3=storage)
  - pInB: Time window in seconds
  - pOut: Statistics value

### K-Bar Data Operations

#### TDXSERVER_SENDKBAR (ID: 16)
- **Purpose**: Send single K-bar data to QuantServer
- **Parameters**:
  - pInA: Symbol/timestamp encoding
  - pInB: OHLC data part 1 (open*10000 + high)
  - pInC: OHLC data part 2 (low*10000 + close)
  - pOut: Send result (1=success, 0=failed, -1=error, -2=server unavailable)
- **ZeroMQ Integration**: Uses `testSingleKBar()` method
- **Data Format**: Creates KBarData structure for server

#### TDXSERVER_SENDKBARSERIES (ID: 20)
- **Purpose**: Send K-bar series data to QuantServer
- **Parameters**:
  - pInA: Price data (close prices)
  - pInB: Volume data
  - pInC: Symbol encoding
  - pOut: Send result
- **ZeroMQ Integration**: Uses `testKBarSeries()` method

### Technical Indicator Calculations

#### TDXSERVER_CALCULATESMA (ID: 17)
- **Purpose**: Calculate Simple Moving Average using QuantServer
- **Parameters**:
  - pInA: Price data array
  - pInB: Period
  - pOut: SMA values
- **ZeroMQ Integration**: Uses `calculateSMA()` method
- **Fallback**: Local SMA calculation if server unavailable

#### TDXSERVER_CALCULATERSI (ID: 18)
- **Purpose**: Calculate RSI using QuantServer
- **Parameters**:
  - pInA: Price data array
  - pInB: Period (default: 14)
  - pOut: RSI values (0-100)
- **ZeroMQ Integration**: Uses `calculateRSI()` method
- **Fallback**: Returns default value 50.0 if server unavailable

#### TDXSERVER_CALCULATEEMA (ID: 21)
- **Purpose**: Calculate Exponential Moving Average using QuantServer
- **Parameters**:
  - pInA: Price data array
  - pInB: Period (default: 12)
  - pOut: EMA values
- **ZeroMQ Integration**: Uses `calculateEMA()` method
- **Fallback**: Local EMA calculation using alpha = 2/(period+1)

#### TDXSERVER_CALCULATEBOLLINGER (ID: 19)
- **Purpose**: Calculate Bollinger Bands using QuantServer
- **Parameters**:
  - pInA: Price data array
  - pInB: Period (default: 20)
  - pInC: Standard deviation multiplier * 100 (default: 200 = 2.0)
  - pOut: Bollinger Band values (middle band)
- **ZeroMQ Integration**: Uses `testBollingerBands()` method
- **Fallback**: Returns input prices if server unavailable

### Parameter Management

#### TDXSERVER_SETPARAMETER (ID: 22)
- **Purpose**: Set QuantServer parameters
- **Parameters**:
  - pInA: Parameter type (0=timeout, 1=max_connections, 2=log_level, 3=precision)
  - pInB: Parameter value
  - pOut: Operation result (1=success, 0=failed, -1=error, -2=server unavailable)
- **ZeroMQ Integration**: Uses `setParameter()` method

#### TDXSERVER_GETPARAMETER (ID: 23)
- **Purpose**: Get QuantServer parameters
- **Parameters**:
  - pInA: Parameter type
  - pOut: Parameter value
- **ZeroMQ Integration**: Uses `getParameter()` method

## Error Handling

### Return Codes
- **1.0**: Success
- **0.0**: Operation failed
- **-1.0**: Exception occurred
- **-2.0**: Server not available/connected
- **-3.0**: Invalid response format
- **-4.0**: Parameter not found

### Fallback Mechanisms
1. **Connection Failure**: Functions attempt local calculations when possible
2. **Server Timeout**: Returns error codes or default values
3. **Invalid Response**: Logs error and returns fallback values
4. **Exception Handling**: Comprehensive try-catch blocks with logging

## Usage in TDX

### Test File Integration
The `JK_TestDll.txt` file provides comprehensive testing of all server functions:

```tdx
{Test ZeroMQ server heartbeat}
心跳响应:=TDXDLL1(10,TIME,0,0);

{Calculate SMA using QuantServer}
SMA指标:=TDXDLL1(17,C,20,0);

{Send K-bar data to QuantServer}
K线发送结果:=TDXDLL1(16,TIME,O*10000+H,L*10000+C);
```

### Performance Monitoring
The test file includes comprehensive performance monitoring:
- ZeroMQ connection quality
- Data transmission efficiency
- Indicator calculation accuracy
- Server resource utilization

## Configuration

### Server Connection
- **Default Host**: localhost
- **Default Port**: 5555
- **Protocol**: ZeroMQ REQ-REP pattern
- **Timeout**: Configurable via parameters

### QuantServer Requirements
1. Python ZeroMQ server running on specified port
2. Support for all indicator calculations (SMA, EMA, RSI, MACD, Bollinger Bands)
3. K-bar data processing capabilities
4. Parameter management interface

## Logging

All server operations are logged with appropriate levels:
- **DEBUG**: Successful operations and detailed information
- **ERROR**: Failed operations, exceptions, and connection issues
- **INFO**: Connection status changes and important events

## Best Practices

1. **Connection Management**: Always check server connectivity before operations
2. **Error Handling**: Implement comprehensive fallback mechanisms
3. **Performance**: Use server calculations for complex indicators, local for simple ones
4. **Monitoring**: Regular heartbeat checks to ensure server availability
5. **Resource Management**: Proper cleanup of ZMQ client resources

## Future Enhancements

1. **Additional Indicators**: MACD, Stochastic, Williams %R
2. **Batch Processing**: Multiple indicator calculations in single request
3. **Caching**: Local caching of frequently used calculations
4. **Load Balancing**: Multiple QuantServer instances for high availability
5. **Security**: Authentication and encryption for production use 