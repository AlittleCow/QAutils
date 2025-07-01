#include "TdxServerFunc.h"
#include "../core/TdxFunctionRegistry.h"
#include "../utils/log.h"
#include "ServerApi.h"
#include <cstring>
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <thread>
#include <chrono>

// TDX Server Function ID offset (starting after common functions)
constexpr int TDX_SERVER_FUNCTION_ID_OFFSET = 10;

// Static member initialization
std::unique_ptr<ServerManager> ServerManager::s_instance = nullptr;

// ============================================================================
// ServerStatus Implementation
// ============================================================================

/**
 * @brief Default constructor for ServerStatus
 */
ServerStatus::ServerStatus()
    : isRunning(true), connectionCount(0), startTime(std::time(nullptr)), version("1.0.0"), uptime(0.0)
{
}

/**
 * @brief Constructor with parameters for ServerStatus
 * @param running Server running status
 * @param connections Number of connections
 * @param start Start time
 * @param ver Version string
 */
ServerStatus::ServerStatus(bool running, int connections, std::time_t start, const std::string& ver)
    : isRunning(running), connectionCount(connections), startTime(start), version(ver), uptime(0.0)
{
}

// ============================================================================
// ServerManager Implementation
// ============================================================================

/**
 * @brief Private constructor for ServerManager singleton
 */
ServerManager::ServerManager()
    : m_startTime(std::time(nullptr)), m_zmqClient(nullptr)
{
    m_status = ServerStatus(true, 0, m_startTime, "TDX-Server-1.0.0");
    
    // Initialize ZMQ client for server communication
    try {
        m_zmqClient = std::make_unique<QAUtils::ZmqClient>("localhost", 5555);
        if (m_zmqClient->connect()) {
            log_debug("ZMQ client connected to QuantServer successfully");
        } else {
            log_error("Failed to connect ZMQ client to QuantServer");
        }
    } catch (const std::exception& e) {
        log_error("Exception initializing ZMQ client: %s", e.what());
        m_zmqClient = nullptr;
    }
}

/**
 * @brief Destructor for ServerManager
 */
ServerManager::~ServerManager()
{
    if (m_zmqClient) {
        m_zmqClient->disconnect();
    }
}

/**
 * @brief Get singleton instance of ServerManager
 * @return Reference to the singleton ServerManager instance
 */
ServerManager& ServerManager::GetInstance()
{
    if (!s_instance)
    {
        s_instance.reset(new ServerManager());
    }
    return *s_instance;
}

/**
 * @brief Get current server status
 * @return Current ServerStatus object
 */
const ServerStatus& ServerManager::GetStatus() const
{
    return m_status;
}

/**
 * @brief Update server status
 * @param status New server status
 */
void ServerManager::UpdateStatus(const ServerStatus& status)
{
    m_status = status;
}

/**
 * @brief Increment connection count
 */
void ServerManager::IncrementConnections()
{
    m_status.connectionCount++;
    log_debug("Connection count incremented to: %d", m_status.connectionCount);
}

/**
 * @brief Decrement connection count
 */
void ServerManager::DecrementConnections()
{
    if (m_status.connectionCount > 0)
    {
        m_status.connectionCount--;
    }
    log_debug("Connection count decremented to: %d", m_status.connectionCount);
}

/**
 * @brief Get server uptime in seconds
 * @return Uptime in seconds
 */
double ServerManager::GetUptime() const
{
    std::time_t currentTime = std::time(nullptr);
    return std::difftime(currentTime, m_startTime);
}

/**
 * @brief Reset server statistics
 */
void ServerManager::Reset()
{
    m_startTime = std::time(nullptr);
    m_status = ServerStatus(true, 0, m_startTime, "TDX-Server-1.0.0");
    log_debug("Server statistics reset");
}

/**
 * @brief Get ZMQ client instance
 * @return Pointer to ZMQ client or nullptr if not available
 */
QAUtils::ZmqClient* ServerManager::GetZmqClient()
{
    return m_zmqClient.get();
}

/**
 * @brief Check if server is connected
 * @return true if ZMQ client is connected to QuantServer
 */
bool ServerManager::IsServerConnected() const
{
    return m_zmqClient && m_zmqClient->isConnected();
}

/**
 * @brief Reconnect to server if disconnected
 * @return true if connection successful
 */
bool ServerManager::ReconnectToServer()
{
    if (m_zmqClient) {
        if (!m_zmqClient->isConnected()) {
            log_debug("Attempting to reconnect to QuantServer...");
            bool success = m_zmqClient->reconnect();
            if (success) {
                log_debug("Successfully reconnected to QuantServer");
            } else {
                log_error("Failed to reconnect to QuantServer, will retry later");
            }
            return success;
        } else {
            log_debug("ZMQ client already connected");
            return true;
        }
    } else {
        log_error("ZMQ client not initialized, cannot reconnect");
        return false;
    }
}

// ============================================================================
// TDX API Function Implementations
// ============================================================================

/**
 * @brief TDX API function for server heartbeat/ping
 * @param DataLen Number of data points
 * @param pfOUT Output array (heartbeat response)
 * @param pfINa Input array A (client timestamp)
 * @param pfINb Input array B (unused)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_Heartbeat)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    for (int i = 0; i < DataLen; i++)
    {
        if (client && client->isConnected()) {
            try {
                json response = client->testHeartbeat();
                if (response.contains("status") && response["status"] == "success") {
                    pfOUT[i] = 1.0f; // Success
                    log_debug("Heartbeat successful: %s", response.dump().c_str());
                } else {
                    pfOUT[i] = 0.0f; // Failed
                    log_error("Heartbeat failed: %s", response.dump().c_str());
                }
            } catch (const std::exception& e) {
                pfOUT[i] = -1.0f; // Error
                log_error("Heartbeat exception: %s", e.what());
            }
        } else {
            // Fallback to local simulation if server not available
            std::time_t serverTime = std::time(nullptr);
            float clientTimestamp = pfINa[i];
            float responseTime = static_cast<float>(serverTime);
            float rtt = responseTime - clientTimestamp;
            pfOUT[i] = responseTime + (rtt * 0.5f);
            log_debug("Heartbeat (local): Client=%f, Server=%f, RTT=%f", 
                     clientTimestamp, responseTime, rtt);
        }
    }
}

/**
 * @brief TDX API function to get server information
 * @param DataLen Number of data points
 * @param pfOUT Output array (server info encoded)
 * @param pfINa Input array A (info type: 0=status, 1=version, 2=uptime, 3=connections)
 * @param pfINb Input array B (unused)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_GetInfo)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    const ServerStatus& status = manager.GetStatus();
    
    for (int i = 0; i < DataLen; i++)
    {
        int infoType = static_cast<int>(pfINa[i]);
        
        if (client && client->isConnected()) {
            try {
                json response = client->getServerInfo();
                if (response.contains("status") && response["status"] == "success") {
                    auto info = response["info"];
                    
                    switch (infoType) {
                        case 0: // Server running status
                            pfOUT[i] = info.value("running", false) ? 1.0f : 0.0f;
                            break;
                        case 1: // Version (encoded as float)
                            pfOUT[i] = 1.0f; // Version 1.0
                            break;
                        case 2: // Uptime in seconds
                            pfOUT[i] = static_cast<float>(manager.GetUptime());
                            break;
                        case 3: // Connection count
                            pfOUT[i] = static_cast<float>(status.connectionCount);
                            break;
                        default:
                            pfOUT[i] = -1.0f; // Invalid info type
                            break;
                    }
                } else {
                    pfOUT[i] = -2.0f; // Server error
                }
            } catch (const std::exception& e) {
                pfOUT[i] = -3.0f; // Exception
                log_error("GetInfo exception: %s", e.what());
            }
        } else {
            // Fallback to local data if server not available
            switch (infoType) {
                case 0: // Server running status
                    pfOUT[i] = status.isRunning ? 1.0f : 0.0f;
                    break;
                case 1: // Version (encoded as float)
                    pfOUT[i] = 1.0f; // Version 1.0
                    break;
                case 2: // Uptime in seconds
                    pfOUT[i] = static_cast<float>(manager.GetUptime());
                    break;
                case 3: // Connection count
                    pfOUT[i] = static_cast<float>(status.connectionCount);
                    break;
                default:
                    pfOUT[i] = -1.0f; // Invalid info type
                    break;
            }
        }
        
        log_debug("GetInfo: Type=%d, Value=%f", infoType, pfOUT[i]);
    }
}

/**
 * @brief TDX API function to simulate connection establishment
 * @param DataLen Number of data points
 * @param pfOUT Output array (connection result)
 * @param pfINa Input array A (client ID)
 * @param pfINb Input array B (connection timeout)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_Connect)
{
    ServerManager& manager = ServerManager::GetInstance();
    
    for (int i = 0; i < DataLen; i++)
    {
        float clientId = pfINa[i];
        float timeout = pfINb[i];
        
        // Simulate connection logic
        bool connectionSuccess = true;
        
        // Simple validation: client ID should be positive and timeout reasonable
        if (clientId <= 0 || timeout <= 0 || timeout > 300) // Max 5 minutes timeout
        {
            connectionSuccess = false;
        }
        
        // Try to ensure server connection
        if (!manager.IsServerConnected()) {
            manager.ReconnectToServer();
        }
        
        if (connectionSuccess)
        {
            manager.IncrementConnections();
            pfOUT[i] = clientId; // Return client ID as confirmation
        }
        else
        {
            pfOUT[i] = -1.0f; // Connection failed
        }
        
        log_debug("Connect: ClientID=%f, Timeout=%f, Success=%d", 
                 clientId, timeout, connectionSuccess ? 1 : 0);
    }
}

/**
 * @brief TDX API function to simulate connection disconnection
 * @param DataLen Number of data points
 * @param pfOUT Output array (disconnection result)
 * @param pfINa Input array A (client ID)
 * @param pfINb Input array B (unused)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_Disconnect)
{
    ServerManager& manager = ServerManager::GetInstance();
    
    for (int i = 0; i < DataLen; i++)
    {
        float clientId = pfINa[i];
        
        // Simulate disconnection logic
        bool disconnectSuccess = true;
        
        if (clientId <= 0)
        {
            disconnectSuccess = false;
        }
        
        if (disconnectSuccess)
        {
            manager.DecrementConnections();
            pfOUT[i] = 0.0f; // Success
        }
        else
        {
            pfOUT[i] = -1.0f; // Disconnect failed
        }
        
        log_debug("Disconnect: ClientID=%f, Success=%d", 
                 clientId, disconnectSuccess ? 1 : 0);
    }
}

/**
 * @brief TDX API function to validate data integrity
 * @param DataLen Number of data points
 * @param pfOUT Output array (validation result)
 * @param pfINa Input array A (data to validate)
 * @param pfINb Input array B (expected checksum)
 * @param pfINc Input array C (validation type)
 */
TDX_EXPORT(TdxServer_ValidateData)
{
    for (int i = 0; i < DataLen; i++)
    {
        float data = pfINa[i];
        float expectedChecksum = pfINb[i];
        int validationType = static_cast<int>(pfINc[i]);
        
        float calculatedChecksum = 0.0f;
        
        switch (validationType)
        {
            case 0: // Simple sum validation
                calculatedChecksum = data;
                break;
            case 1: // Square validation
                calculatedChecksum = data * data;
                break;
            case 2: // Absolute value validation
                calculatedChecksum = std::abs(data);
                break;
            default:
                calculatedChecksum = -1.0f; // Invalid validation type
                break;
        }
        
        // Check if calculated checksum matches expected
        float tolerance = 0.001f;
        bool isValid = std::abs(calculatedChecksum - expectedChecksum) < tolerance;
        
        pfOUT[i] = isValid ? 1.0f : 0.0f;
        
        log_debug("ValidateData: Data=%f, Expected=%f, Calculated=%f, Valid=%d", 
                 data, expectedChecksum, calculatedChecksum, isValid ? 1 : 0);
    }
}

/**
 * @brief TDX API function to get server statistics
 * @param DataLen Number of data points
 * @param pfOUT Output array (statistics data)
 * @param pfINa Input array A (stat type: 0=memory, 1=cpu, 2=network, 3=storage)
 * @param pfINb Input array B (time window in seconds)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_GetStats)
{
    ServerManager& manager = ServerManager::GetInstance();
    
    for (int i = 0; i < DataLen; i++)
    {
        int statType = static_cast<int>(pfINa[i]);
        float timeWindow = pfINb[i];
        
        // Simulate different statistics based on type
        float statValue = 0.0f;
        
        switch (statType)
        {
            case 0: // Memory usage (simulated as percentage)
                statValue = 65.5f + static_cast<float>(std::sin(manager.GetUptime() / 60.0) * 10.0);
                break;
            case 1: // CPU usage (simulated as percentage)
                statValue = 45.2f + static_cast<float>(std::cos(manager.GetUptime() / 30.0) * 15.0);
                break;
            case 2: // Network throughput (simulated as MB/s)
                statValue = 128.0f + static_cast<float>(std::sin(manager.GetUptime() / 120.0) * 32.0);
                break;
            case 3: // Storage usage (simulated as percentage)
                statValue = 78.3f + static_cast<float>(manager.GetUptime() / 86400.0); // Slowly increasing over time
                break;
            default:
                statValue = -1.0f; // Invalid stat type
                break;
        }
        
        // Apply time window factor (simulate different values for different windows)
        if (timeWindow > 0)
        {
            statValue *= (1.0f + (timeWindow / 3600.0f) * 0.1f); // Slight variation based on time window
        }
        
        pfOUT[i] = statValue;
        
        log_debug("GetStats: Type=%d, TimeWindow=%f, Value=%f", 
                 statType, timeWindow, statValue);
    }
}

/**
 * @brief TDX API function to send single K-bar data to server
 * @param DataLen Number of data points
 * @param pfOUT Output array (server response)
 * @param pfINa Input array A (encoded symbol and timestamp)
 * @param pfINb Input array B (OHLC data packed: open*10000 + high)
 * @param pfINc Input array C (OHLC data packed: low*10000 + close, volume in high 16 bits)
 */
TDX_EXPORT(TdxServer_SendKBar)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    for (int i = 0; i < DataLen; i++)
    {
        if (client && client->isConnected()) {
            try {
                // Decode input data
                float symbolTimestamp = pfINa[i];
                float ohlcData1 = pfINb[i];
                float ohlcData2 = pfINc[i];
                
                // Extract OHLC values (simplified encoding)
                int encoded1 = static_cast<int>(ohlcData1);
                int encoded2 = static_cast<int>(ohlcData2);
                
                float open = (encoded1 / 10000) / 100.0f;
                float high = (encoded1 % 10000) / 100.0f;
                float low = (encoded2 / 10000) / 100.0f;
                float close = (encoded2 % 10000) / 100.0f;
                long volume = static_cast<long>(symbolTimestamp * 1000); // Simplified volume
                
                // Create K-bar data
                QAUtils::KBarData kbar;
                kbar.symbol = "TEST" + std::to_string(static_cast<int>(symbolTimestamp));
                kbar.timestamp = "2024-01-01T10:00:00Z"; // Simplified timestamp
                kbar.open = open;
                kbar.high = high;
                kbar.low = low;
                kbar.close = close;
                kbar.volume = volume;
                
                json response = client->testSingleKBar(kbar);
                if (response.contains("status") && response["status"] == "success") {
                    pfOUT[i] = 1.0f; // Success
                    log_debug("KBar sent successfully");
                } else {
                    pfOUT[i] = 0.0f; // Failed
                    log_error("KBar send failed: %s", response.dump().c_str());
                }
            } catch (const std::exception& e) {
                pfOUT[i] = -1.0f; // Error
                log_error("SendKBar exception: %s", e.what());
            }
        } else {
            pfOUT[i] = -2.0f; // Server not available
            log_error("SendKBar: Server not connected");
        }
    }
}

/**
 * @brief TDX API function to calculate Simple Moving Average
 * @param DataLen Number of data points
 * @param pfOUT Output array (SMA values)
 * @param pfINa Input array A (price data)
 * @param pfINb Input array B (period)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_CalculateSMA)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    if (client && client->isConnected()) {
        try {
            // Collect price data
            std::vector<double> priceData;
            for (int i = 0; i < DataLen; i++) {
                priceData.push_back(static_cast<double>(pfINa[i]));
            }
            
            int period = static_cast<int>(pfINb[0]); // Use first element as period
            if (period <= 0) period = 20; // Default period
            
            json response = client->calculateSMA(priceData, period);
            if (response.contains("status") && response["status"] == "success") {
                auto results = response["results"];
                if (!results.empty() && results[0].contains("result")) {
                    auto smaValues = results[0]["result"]["values"];
                    
                    // Fill output array
                    for (int i = 0; i < DataLen; i++) {
                        if (i < static_cast<int>(smaValues.size())) {
                            pfOUT[i] = static_cast<float>(smaValues[i]);
                        } else {
                            pfOUT[i] = 0.0f; // Pad with zeros
                        }
                    }
                    log_debug("SMA calculated successfully, period=%d", period);
                } else {
                    // Fill with zeros on error
                    for (int i = 0; i < DataLen; i++) {
                        pfOUT[i] = 0.0f;
                    }
                    log_error("SMA calculation failed: invalid response format");
                }
            } else {
                // Fill with zeros on error
                for (int i = 0; i < DataLen; i++) {
                    pfOUT[i] = 0.0f;
                }
                log_error("SMA calculation failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            // Fill with zeros on exception
            for (int i = 0; i < DataLen; i++) {
                pfOUT[i] = 0.0f;
            }
            log_error("SMA calculation exception: %s", e.what());
        }
    } else {
        // Simple local SMA calculation as fallback
        int period = static_cast<int>(pfINb[0]);
        if (period <= 0) period = 20;
        
        for (int i = 0; i < DataLen; i++) {
            if (i < period - 1) {
                pfOUT[i] = 0.0f; // Not enough data
            } else {
                float sum = 0.0f;
                for (int j = i - period + 1; j <= i; j++) {
                    sum += pfINa[j];
                }
                pfOUT[i] = sum / period;
            }
        }
        log_debug("SMA calculated locally (fallback), period=%d", period);
    }
}

/**
 * @brief TDX API function to calculate RSI (Relative Strength Index)
 * @param DataLen Number of data points
 * @param pfOUT Output array (RSI values)
 * @param pfINa Input array A (price data)
 * @param pfINb Input array B (period)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_CalculateRSI)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    if (client && client->isConnected()) {
        try {
            // Collect price data
            std::vector<double> priceData;
            for (int i = 0; i < DataLen; i++) {
                priceData.push_back(static_cast<double>(pfINa[i]));
            }
            
            int period = static_cast<int>(pfINb[0]); // Use first element as period
            if (period <= 0) period = 14; // Default period
            
            json response = client->calculateRSI(priceData, period);
            if (response.contains("status") && response["status"] == "success") {
                auto results = response["results"];
                if (!results.empty() && results[0].contains("result")) {
                    auto rsiValues = results[0]["result"]["values"];
                    
                    // Fill output array
                    for (int i = 0; i < DataLen; i++) {
                        if (i < static_cast<int>(rsiValues.size())) {
                            pfOUT[i] = static_cast<float>(rsiValues[i]);
                        } else {
                            pfOUT[i] = 50.0f; // Default RSI value
                        }
                    }
                    log_debug("RSI calculated successfully, period=%d", period);
                } else {
                    // Fill with default values on error
                    for (int i = 0; i < DataLen; i++) {
                        pfOUT[i] = 50.0f;
                    }
                    log_error("RSI calculation failed: invalid response format");
                }
            } else {
                // Fill with default values on error
                for (int i = 0; i < DataLen; i++) {
                    pfOUT[i] = 50.0f;
                }
                log_error("RSI calculation failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            // Fill with default values on exception
            for (int i = 0; i < DataLen; i++) {
                pfOUT[i] = 50.0f;
            }
            log_error("RSI calculation exception: %s", e.what());
        }
    } else {
        // Fill with default values if server not available
        for (int i = 0; i < DataLen; i++) {
            pfOUT[i] = 50.0f; // Default RSI value
        }
        log_debug("RSI: Server not connected, using default values");
    }
}

/**
 * @brief TDX API function to calculate Bollinger Bands
 * @param DataLen Number of data points
 * @param pfOUT Output array (encoded Bollinger Bands data)
 * @param pfINa Input array A (price data)
 * @param pfINb Input array B (period)
 * @param pfINc Input array C (standard deviation multiplier * 100)
 */
TDX_EXPORT(TdxServer_CalculateBollinger)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    if (client && client->isConnected()) {
        try {
            // Collect price data
            std::vector<double> priceData;
            for (int i = 0; i < DataLen; i++) {
                priceData.push_back(static_cast<double>(pfINa[i]));
            }
            
            int period = static_cast<int>(pfINb[0]);
            if (period <= 0) period = 20; // Default period
            
            double stdDev = static_cast<double>(pfINc[0]) / 100.0; // Convert from scaled value
            if (stdDev <= 0) stdDev = 2.0; // Default std dev
            
            json response = client->testBollingerBands(priceData, period, stdDev);
            if (response.contains("status") && response["status"] == "success") {
                auto results = response["results"];
                if (!results.empty() && results[0].contains("result")) {
                    auto bollinger = results[0]["result"];
                    auto upperBand = bollinger["upper_band"];
                    auto middleBand = bollinger["middle_band"];
                    auto lowerBand = bollinger["lower_band"];
                    
                    // Encode bands into output (simplified: use middle band)
                    for (int i = 0; i < DataLen; i++) {
                        if (i < static_cast<int>(middleBand.size())) {
                            pfOUT[i] = static_cast<float>(middleBand[i]);
                        } else {
                            pfOUT[i] = pfINa[i]; // Use input price as fallback
                        }
                    }
                    log_debug("Bollinger Bands calculated successfully, period=%d, stdDev=%f", period, stdDev);
                } else {
                    // Fill with input prices on error
                    for (int i = 0; i < DataLen; i++) {
                        pfOUT[i] = pfINa[i];
                    }
                    log_error("Bollinger Bands calculation failed: invalid response format");
                }
            } else {
                // Fill with input prices on error
                for (int i = 0; i < DataLen; i++) {
                    pfOUT[i] = pfINa[i];
                }
                log_error("Bollinger Bands calculation failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            // Fill with input prices on exception
            for (int i = 0; i < DataLen; i++) {
                pfOUT[i] = pfINa[i];
            }
            log_error("Bollinger Bands calculation exception: %s", e.what());
        }
    } else {
        // Fill with input prices if server not available
        for (int i = 0; i < DataLen; i++) {
            pfOUT[i] = pfINa[i];
        }
        log_debug("Bollinger Bands: Server not connected, using input prices");
    }
}

/**
 * @brief TDX API function to send K-bar series data to server
 * @param DataLen Number of data points
 * @param pfOUT Output array (server response)
 * @param pfINa Input array A (price data - close prices)
 * @param pfINb Input array B (volume data)
 * @param pfINc Input array C (symbol encoding)
 */
TDX_EXPORT(TdxServer_SendKBarSeries)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    if (client && client->isConnected()) {
        try {
            // Create K-bar series from input data
            std::vector<QAUtils::KBarData> kbarSeries;
            std::string symbol = "STOCK" + std::to_string(static_cast<int>(pfINc[0]));
            
            for (int i = 0; i < DataLen; i++) {
                QAUtils::KBarData kbar;
                kbar.symbol = symbol;
                kbar.timestamp = "2024-01-0" + std::to_string((i % 9) + 1) + "T10:00:00Z";
                kbar.close = static_cast<double>(pfINa[i]);
                kbar.open = kbar.close * 0.99; // Simulate open price
                kbar.high = kbar.close * 1.02; // Simulate high price
                kbar.low = kbar.close * 0.98;  // Simulate low price
                kbar.volume = static_cast<long>(pfINb[i]);
                
                kbarSeries.push_back(kbar);
            }
            
            json response = client->testKBarSeries(symbol, kbarSeries);
            if (response.contains("status") && response["status"] == "success") {
                for (int i = 0; i < DataLen; i++) {
                    pfOUT[i] = 1.0f; // Success
                }
                log_debug("K-bar series sent successfully, symbol=%s, count=%d", symbol.c_str(), DataLen);
            } else {
                for (int i = 0; i < DataLen; i++) {
                    pfOUT[i] = 0.0f; // Failed
                }
                log_error("K-bar series send failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            for (int i = 0; i < DataLen; i++) {
                pfOUT[i] = -1.0f; // Error
            }
            log_error("SendKBarSeries exception: %s", e.what());
        }
    } else {
        for (int i = 0; i < DataLen; i++) {
            pfOUT[i] = -2.0f; // Server not available
        }
        log_error("SendKBarSeries: Server not connected");
    }
}

/**
 * @brief TDX API function to calculate EMA (Exponential Moving Average)
 * @param DataLen Number of data points
 * @param pfOUT Output array (EMA values)
 * @param pfINa Input array A (price data)
 * @param pfINb Input array B (period)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_CalculateEMA)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    if (client && client->isConnected()) {
        try {
            // Collect price data
            std::vector<double> priceData;
            for (int i = 0; i < DataLen; i++) {
                priceData.push_back(static_cast<double>(pfINa[i]));
            }
            
            int period = static_cast<int>(pfINb[0]); // Use first element as period
            if (period <= 0) period = 12; // Default period
            
            json response = client->calculateEMA(priceData, period);
            if (response.contains("status") && response["status"] == "success") {
                auto results = response["results"];
                if (!results.empty() && results[0].contains("result")) {
                    auto emaValues = results[0]["result"]["values"];
                    
                    // Fill output array
                    for (int i = 0; i < DataLen; i++) {
                        if (i < static_cast<int>(emaValues.size())) {
                            pfOUT[i] = static_cast<float>(emaValues[i]);
                        } else {
                            pfOUT[i] = pfINa[i]; // Use input price as fallback
                        }
                    }
                    log_debug("EMA calculated successfully, period=%d", period);
                } else {
                    // Fill with input prices on error
                    for (int i = 0; i < DataLen; i++) {
                        pfOUT[i] = pfINa[i];
                    }
                    log_error("EMA calculation failed: invalid response format");
                }
            } else {
                // Fill with input prices on error
                for (int i = 0; i < DataLen; i++) {
                    pfOUT[i] = pfINa[i];
                }
                log_error("EMA calculation failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            // Fill with input prices on exception
            for (int i = 0; i < DataLen; i++) {
                pfOUT[i] = pfINa[i];
            }
            log_error("EMA calculation exception: %s", e.what());
        }
    } else {
        // Simple local EMA calculation as fallback
        int period = static_cast<int>(pfINb[0]);
        if (period <= 0) period = 12;
        
        double alpha = 2.0 / (period + 1);
        pfOUT[0] = pfINa[0]; // First value is the same
        
        for (int i = 1; i < DataLen; i++) {
            pfOUT[i] = static_cast<float>(alpha * pfINa[i] + (1 - alpha) * pfOUT[i-1]);
        }
        log_debug("EMA calculated locally (fallback), period=%d", period);
    }
}

/**
 * @brief TDX API function to set server parameters
 * @param DataLen Number of data points
 * @param pfOUT Output array (operation result)
 * @param pfINa Input array A (parameter type encoded)
 * @param pfINb Input array B (parameter value)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_SetParameter)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    for (int i = 0; i < DataLen; i++) {
        if (client && client->isConnected()) {
            try {
                int paramType = static_cast<int>(pfINa[i]);
                float paramValue = pfINb[i];
                
                std::string paramName;
                json value;
                
                switch (paramType) {
                    case 0:
                        paramName = "server_timeout";
                        value = static_cast<int>(paramValue);
                        break;
                    case 1:
                        paramName = "max_connections";
                        value = static_cast<int>(paramValue);
                        break;
                    case 2:
                        paramName = "log_level";
                        value = static_cast<int>(paramValue);
                        break;
                    case 3:
                        paramName = "calculation_precision";
                        value = static_cast<double>(paramValue);
                        break;
                    default:
                        paramName = "custom_param_" + std::to_string(paramType);
                        value = static_cast<double>(paramValue);
                        break;
                }
                
                json response = client->setParameter(paramName, value);
                if (response.contains("status") && response["status"] == "success") {
                    pfOUT[i] = 1.0f; // Success
                    log_debug("Parameter set successfully: %s = %f", paramName.c_str(), paramValue);
                } else {
                    pfOUT[i] = 0.0f; // Failed
                    log_error("Parameter set failed: %s", response.dump().c_str());
                }
            } catch (const std::exception& e) {
                pfOUT[i] = -1.0f; // Error
                log_error("SetParameter exception: %s", e.what());
            }
        } else {
            pfOUT[i] = -2.0f; // Server not available
        }
    }
}

/**
 * @brief TDX API function to get server parameters
 * @param DataLen Number of data points
 * @param pfOUT Output array (parameter values)
 * @param pfINa Input array A (parameter type encoded)
 * @param pfINb Input array B (unused)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_GetParameter)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    for (int i = 0; i < DataLen; i++) {
        if (client && client->isConnected()) {
            try {
                int paramType = static_cast<int>(pfINa[i]);
                std::string paramName;
                
                switch (paramType) {
                    case 0:
                        paramName = "server_timeout";
                        break;
                    case 1:
                        paramName = "max_connections";
                        break;
                    case 2:
                        paramName = "log_level";
                        break;
                    case 3:
                        paramName = "calculation_precision";
                        break;
                    default:
                        paramName = "custom_param_" + std::to_string(paramType);
                        break;
                }
                
                json response = client->getParameter(paramName);
                if (response.contains("status") && response["status"] == "success") {
                    auto param = response["parameter"];
                    if (param.contains("value") && !param["value"].is_null()) {
                        if (param["value"].is_number()) {
                            pfOUT[i] = static_cast<float>(param["value"]);
                        } else {
                            pfOUT[i] = 0.0f; // Non-numeric value
                        }
                    } else {
                        pfOUT[i] = -1.0f; // Parameter not found
                    }
                    log_debug("Parameter retrieved: %s = %f", paramName.c_str(), pfOUT[i]);
                } else {
                    pfOUT[i] = -2.0f; // Server error
                    log_error("Parameter get failed: %s", response.dump().c_str());
                }
            } catch (const std::exception& e) {
                pfOUT[i] = -3.0f; // Exception
                log_error("GetParameter exception: %s", e.what());
            }
        } else {
            pfOUT[i] = -4.0f; // Server not available
        }
    }
}

// ============================================================================
// TDX Function Wrapper Classes
// ============================================================================

/**
 * @brief Wrapper class for TdxServer_Heartbeat function
 */
class TdxServerHeartbeatFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerHeartbeatFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 0, "TdxServer_Heartbeat", "Server heartbeat/ping function", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_Heartbeat
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_Heartbeat;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Client timestamp, pInB=unused, pInC=unused, pOut=Server response time";
    }
};

/**
 * @brief Wrapper class for TdxServer_GetInfo function
 */
class TdxServerGetInfoFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerGetInfoFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 1, "TdxServer_GetInfo", "Get server information", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_GetInfo
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_GetInfo;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Info type (0=status,1=version,2=uptime,3=connections), pInB=unused, pInC=unused, pOut=Info value";
    }
};

/**
 * @brief Wrapper class for TdxServer_Connect function
 */
class TdxServerConnectFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerConnectFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 2, "TdxServer_Connect", "Simulate client connection", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_Connect
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_Connect;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Client ID, pInB=Connection timeout, pInC=unused, pOut=Connection result";
    }
};

/**
 * @brief Wrapper class for TdxServer_Disconnect function
 */
class TdxServerDisconnectFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerDisconnectFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 3, "TdxServer_Disconnect", "Simulate client disconnection", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_Disconnect
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_Disconnect;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Client ID, pInB=unused, pInC=unused, pOut=Disconnection result";
    }
};

/**
 * @brief Wrapper class for TdxServer_ValidateData function
 */
class TdxServerValidateDataFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerValidateDataFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 4, "TdxServer_ValidateData", "Validate data integrity", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_ValidateData
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_ValidateData;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Data to validate, pInB=Expected checksum, pInC=Validation type, pOut=Validation result";
    }
};

/**
 * @brief Wrapper class for TdxServer_GetStats function
 */
class TdxServerGetStatsFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerGetStatsFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 5, "TdxServer_GetStats", "Get server statistics", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_GetStats
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_GetStats;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Stat type (0=memory,1=cpu,2=network,3=storage), pInB=Time window, pInC=unused, pOut=Statistics value";
    }
};

/**
 * @brief Wrapper class for TdxServer_SendKBar function
 */
class TdxServerSendKBarFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerSendKBarFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 6, "TdxServer_SendKBar", "Send K-bar data to server", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_SendKBar
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_SendKBar;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Symbol/timestamp, pInB=OHLC data1, pInC=OHLC data2/volume, pOut=Send result";
    }
};

/**
 * @brief Wrapper class for TdxServer_CalculateSMA function
 */
class TdxServerCalculateSMAFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerCalculateSMAFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 7, "TdxServer_CalculateSMA", "Calculate Simple Moving Average", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_CalculateSMA
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_CalculateSMA;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Price data, pInB=Period, pInC=unused, pOut=SMA values";
    }
};

/**
 * @brief Wrapper class for TdxServer_CalculateRSI function
 */
class TdxServerCalculateRSIFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerCalculateRSIFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 8, "TdxServer_CalculateRSI", "Calculate RSI indicator", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_CalculateRSI
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_CalculateRSI;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Price data, pInB=Period, pInC=unused, pOut=RSI values";
    }
};

/**
 * @brief Wrapper class for TdxServer_CalculateBollinger function
 */
class TdxServerCalculateBollingerFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerCalculateBollingerFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 9, "TdxServer_CalculateBollinger", "Calculate Bollinger Bands", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_CalculateBollinger
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_CalculateBollinger;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Price data, pInB=Period, pInC=Std dev*100, pOut=Bollinger values";
    }
};

/**
 * @brief Wrapper class for TdxServer_SendKBarSeries function
 */
class TdxServerSendKBarSeriesFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerSendKBarSeriesFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 10, "TdxServer_SendKBarSeries", "Send K-bar series data to server", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_SendKBarSeries
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_SendKBarSeries;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Close prices, pInB=Volume data, pInC=Symbol encoding, pOut=Send result";
    }
};

/**
 * @brief Wrapper class for TdxServer_CalculateEMA function
 */
class TdxServerCalculateEMAFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerCalculateEMAFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 11, "TdxServer_CalculateEMA", "Calculate Exponential Moving Average", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_CalculateEMA
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_CalculateEMA;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Price data, pInB=Period, pInC=unused, pOut=EMA values";
    }
};

/**
 * @brief Wrapper class for TdxServer_SetParameter function
 */
class TdxServerSetParameterFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerSetParameterFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 12, "TdxServer_SetParameter", "Set server parameters", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_SetParameter
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_SetParameter;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Parameter type, pInB=Parameter value, pInC=unused, pOut=Operation result";
    }
};

/**
 * @brief Wrapper class for TdxServer_GetParameter function
 */
class TdxServerGetParameterFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerGetParameterFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 13, "TdxServer_GetParameter", "Get server parameters", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_GetParameter
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_GetParameter;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Parameter type, pInB=unused, pInC=unused, pOut=Parameter values";
    }
};

// ============================================================================
// Function Registration
// ============================================================================

/**
 * @brief Register all TDX server functions with the function registry
 * @return true if all functions were registered successfully
 */
bool RegisterTdxServerFunctions()
{
    try
    {
        auto& registry = TdxFunctionRegistry::GetInstance();
        bool success = true;
        
        // Register all server functions
        success &= registry.RegisterFunction(std::make_shared<TdxServerHeartbeatFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerGetInfoFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerConnectFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerDisconnectFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerValidateDataFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerGetStatsFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerSendKBarFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerCalculateSMAFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerCalculateRSIFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerCalculateBollingerFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerSendKBarSeriesFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerCalculateEMAFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerSetParameterFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerGetParameterFunction>());
        
        if (success)
        {
            log_debug("All TDX server functions registered successfully");
        }
        else
        {
            log_error("Some TDX server functions failed to register");
        }
        
        return success;
    }
    catch (const std::exception& e)
    {
        log_error("Exception while registering TDX server functions: %s", e.what());
        return false;
    }
    catch (...)
    {
        log_error("Unknown exception while registering TDX server functions");
        return false;
    }
}
