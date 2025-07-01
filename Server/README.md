# QuantServer - ZeroMQ Based Financial Data Server

A ZeroMQ-based server designed to handle TDX client requests for financial data processing and technical indicator calculations.

## Features

The QuantServer supports four main types of operations:

1. **Kbar Data Processing** - Single kbar or series data handling
2. **Side Band API Calls** - Remote indicator function execution
3. **Result Responses** - Structured responses back to clients
4. **Server Control** - Parameter management and server configuration

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python QAutils/Server/QuantServer.py
```

Or with custom settings:
```bash
python QAutils/Server/QuantServer.py --port 5556 --log-level DEBUG
```

## Usage

### Starting the Server

```python
from QAutils.Server.QuantServer import QuantServer

# Create and start server
server = QuantServer(port=5555)
server.start_server()
```

### Message Types

#### 1. Kbar Data (Single)
```json
{
    "type": "kbar_data",
    "data": {
        "symbol": "AAPL",
        "timestamp": "2024-01-15T10:30:00",
        "open": 150.25,
        "high": 151.80,
        "low": 149.90,
        "close": 151.50,
        "volume": 1000000
    }
}
```

#### 2. Kbar Series Data
```json
{
    "type": "kbar_series",
    "symbol": "AAPL",
    "data": [
        {
            "timestamp": "2024-01-15T10:00:00",
            "open": 150.00,
            "high": 150.50,
            "low": 149.50,
            "close": 150.25,
            "volume": 500000
        }
    ]
}
```

#### 3. API Calls (Indicators)
```json
{
    "type": "api_call",
    "requests": [
        {
            "indicator_name": "Simple Moving Average",
            "indicator_function_name": "sma",
            "parameters": {
                "data": [100, 102, 101, 103, 105],
                "period": 5
            },
            "result_required": true
        }
    ]
}
```

#### 4. Control Messages
```json
{
    "type": "control",
    "control_type": "set_param",
    "parameters": {
        "name": "max_connections",
        "value": 100
    }
}
```

### Available Indicators

The server includes the following built-in technical indicators:

- **SMA** - Simple Moving Average
- **EMA** - Exponential Moving Average  
- **RSI** - Relative Strength Index
- **MACD** - Moving Average Convergence Divergence
- **Bollinger Bands** - Bollinger Bands

### Control Commands

- `set_param` - Set server parameter
- `get_param` - Get server parameter
- `get_all_params` - Get all server parameters
- `server_info` - Get server information

## Example Client

Run the example client to test all functionality:

```bash
python example_client.py
```

This will test:
- Heartbeat messages
- Single kbar data processing
- Kbar series processing
- Indicator calculations
- Server control operations

## Custom Indicators

You can register custom indicator functions:

```python
def my_custom_indicator(params):
    data = params.get('data', [])
    # Your calculation logic here
    return {'indicator': 'Custom', 'values': [...]}

server.register_indicator('custom', my_custom_indicator)
```

## Error Handling

The server provides comprehensive error handling and logging. All responses include:
- Status (success/error)
- Timestamp
- Error messages and tracebacks when applicable

## Message Format

All messages follow a consistent JSON format:

**Request Format:**
```json
{
    "type": "message_type",
    "data": {...},
    "parameters": {...}
}
```

**Response Format:**
```json
{
    "status": "success|error",
    "type": "response_type",
    "data": {...},
    "timestamp": "2024-01-15T10:30:00.000000"
}
```

## Architecture

- **ZeroMQ REP-REQ Pattern** - Reliable request-response communication
- **JSON Message Format** - Human-readable and language-agnostic
- **Modular Design** - Easy to extend with new indicators and features
- **Comprehensive Logging** - Full request/response tracking
- **Error Recovery** - Graceful handling of malformed requests

## Performance

The server is designed for high-performance financial data processing:
- Asynchronous message handling
- Efficient indicator calculations
- Memory-conscious data processing
- Configurable timeouts and limits 