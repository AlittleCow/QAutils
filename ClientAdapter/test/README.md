# ZmqClient - C++ Client for QuantServer

This is a C++ implementation of a ZeroMQ client that communicates with the Python QuantServer. It provides the same functionality as the Python `example_client.py` but in C++.

## Features

The ZmqClient class supports all the API calls demonstrated in the Python example client:

- **Heartbeat**: Test connectivity with the server
- **K-bar Data**: Send single K-bar data or series to the server
- **API Calls**: Execute indicator calculations (SMA, RSI, EMA, Bollinger Bands)
- **Control Messages**: Server parameter management and information retrieval

## Dependencies

Before building, you need to install the following dependencies:

### Required Libraries

1. **ZeroMQ C++ bindings (cppzmq)**
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install libzmq3-dev libcppzmq-dev
   
   # On macOS with Homebrew
   brew install zeromq cppzmq
   
   # On Windows with vcpkg
   vcpkg install cppzmq
   ```

2. **nlohmann/json**
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install nlohmann-json3-dev
   
   # On macOS with Homebrew
   brew install nlohmann-json
   
   # On Windows with vcpkg
   vcpkg install nlohmann-json
   ```

## Building

### Using CMake

```bash
mkdir build
cd build
cmake ..
make
```

### Manual Compilation

If you prefer to compile manually:

```bash
g++ -std=c++17 -I/usr/include/nlohmann \
    ServerApi.cpp example_usage.cpp \
    -lzmq -o example_usage
```

## Usage

### Basic Usage

```cpp
#include "ServerApi.h"
using namespace QAUtils;

int main() {
    // Create client instance
    ZmqClient client("localhost", 5555);
    
    // Connect to server
    if (!client.connect()) {
        std::cerr << "Failed to connect to server" << std::endl;
        return 1;
    }
    
    // Test heartbeat
    auto response = client.testHeartbeat();
    std::cout << "Response: " << response.dump(2) << std::endl;
    
    return 0;
}
```

### K-bar Data Example

```cpp
// Single K-bar
KBarData kbar = {
    "AAPL",                    // symbol
    "2024-01-15T10:30:00",     // timestamp
    150.25,                    // open
    151.80,                    // high
    149.90,                    // low
    151.50,                    // close
    1000000                    // volume
};
auto response = client.testSingleKBar(kbar);

// K-bar series
std::vector<KBarData> series = { /* multiple K-bars */ };
auto series_response = client.testKBarSeries("AAPL", series);
```

### Indicator Calculations

```cpp
std::vector<double> prices = {100, 102, 101, 103, 105, 104, 106, 108};

// Simple Moving Average
auto sma_response = client.calculateSMA(prices, 5);

// RSI
auto rsi_response = client.calculateRSI(prices, 14);

// Bollinger Bands
auto bb_response = client.testBollingerBands(prices, 20, 2.0);
```

### Control Messages

```cpp
// Set parameter
client.setParameter("max_connections", 100);

// Get parameter
auto param = client.getParameter("max_connections");

// Get server info
auto info = client.getServerInfo();

// Get all parameters
auto all_params = client.getAllParameters();
```

## API Reference

### Main Methods

- `bool connect()` - Connect to the QuantServer
- `void disconnect()` - Disconnect from server
- `bool isConnected()` - Check connection status
- `json sendRequest(const json& message)` - Send raw JSON request

### Test Methods

- `json testHeartbeat()` - Test server connectivity
- `json testSingleKBar(const KBarData& kbar_data)` - Send single K-bar
- `json testKBarSeries(const string& symbol, const vector<KBarData>& series)` - Send K-bar series
- `json testApiCalls(const vector<ApiRequest>& requests)` - Execute API calls

### Indicator Methods

- `json calculateSMA(const vector<double>& data, int period)` - Simple Moving Average
- `json calculateRSI(const vector<double>& data, int period)` - RSI calculation
- `json calculateEMA(const vector<double>& data, int period)` - Exponential Moving Average
- `json testBollingerBands(const vector<double>& data, int period, double std_dev)` - Bollinger Bands

### Control Methods

- `json setParameter(const string& name, const json& value)` - Set server parameter
- `json getParameter(const string& name)` - Get server parameter
- `json getServerInfo()` - Get server information
- `json getAllParameters()` - Get all server parameters

## Data Structures

### KBarData
```cpp
struct KBarData {
    std::string symbol;      // Symbol name
    std::string timestamp;   // ISO format timestamp
    double open;            // Opening price
    double high;            // High price
    double low;             // Low price
    double close;           // Closing price
    long volume;            // Volume
};
```

### ApiRequest
```cpp
struct ApiRequest {
    std::string indicator_name;           // Display name of indicator
    std::string indicator_function_name;  // Function name on server
    json parameters;                      // Parameters for the function
    bool result_required;                 // Whether result is required
};
```

## Running the Example

1. Make sure the Python QuantServer is running:
   ```bash
   cd QAutils/Server
   python QuantServer.py
   ```

2. Run the C++ example:
   ```bash
   ./example_usage
   ```

## Notes

- The client uses REQ-REP socket pattern (synchronous)
- All messages are JSON formatted
- The client automatically handles JSON serialization/deserialization
- Connection cleanup is handled automatically in the destructor
- Error handling provides meaningful error messages

## Compatibility

This client is compatible with the Python QuantServer and supports all message types defined in the server protocol. 