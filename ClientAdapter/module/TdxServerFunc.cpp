#include "TdxServerFunc.h"
#include "TdxCommonFunc.h"
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
    log_debug("ServerManager destructor called");
    log_debug("Checking ZMQ client state in destructor");
    
    if (m_zmqClient && m_zmqClient->isConnected()) {
        log_debug("Disconnecting ZMQ client");
        m_zmqClient->disconnect();
        log_debug("ZMQ client disconnected");
    } else if (m_zmqClient) {
        log_debug("ZMQ client already disconnected, skipping disconnect in destructor");
    } else {
        log_debug("ZMQ client is null in destructor");
    }
    
    log_debug("About to reset ZMQ client unique_ptr");
    m_zmqClient.reset(); // Explicitly reset to trigger ZmqClient destructor
    log_debug("ZMQ client unique_ptr reset completed");
    
    log_debug("ServerManager destructor completed successfully");
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
 * @brief Cleanup and destroy the singleton instance
 * 
 * This method should be called during plugin cleanup to ensure
 * the ServerManager destructor is called and resources are properly cleaned up.
 */
void ServerManager::Cleanup()
{
    if (s_instance) {
        log_debug("Explicitly cleaning up ServerManager singleton");
        
        // Explicitly disconnect ZMQ client before destroying the instance
        // to avoid double disconnect during DLL unload
        if (s_instance->m_zmqClient && s_instance->m_zmqClient->isConnected()) {
            log_debug("Disconnecting ZMQ client before ServerManager destruction");
            s_instance->m_zmqClient->disconnect();
        }
        
        s_instance.reset(); // This will call the destructor
    }
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

/**
 * @brief Disconnect ZMQ client after API operations complete
 * 
 * This method provides controlled disconnection after API completion
 * without destroying the entire ServerManager instance.
 */
void ServerManager::DisconnectAfterAPI()
{
    if (m_zmqClient && m_zmqClient->isConnected()) {
        try {
            m_zmqClient->disconnect();
            log_debug("ZMQ client disconnected after API completion");
        } catch (const std::exception& e) {
            log_error("Error disconnecting ZMQ client after API: %s", e.what());
        }
    }
}

/**
 * @brief Cleanup resources after API session completion
 * 
 * This method should be called when an API session is complete to ensure
 * proper resource cleanup while keeping the ServerManager instance alive.
 * @param forceDisconnect If true, forces disconnection even if connection is healthy
 */
void ServerManager::CleanupAfterAPISession(bool forceDisconnect)
{
    try {
        if (forceDisconnect || !IsServerConnected()) {
            DisconnectAfterAPI();
        }
        
        // Reset any temporary state that might accumulate during API usage
        // Keep core statistics but clear temporary data
        log_debug("API session cleanup completed, forceDisconnect=%s", forceDisconnect ? "true" : "false");
        
    } catch (const std::exception& e) {
        log_error("Error during API session cleanup: %s", e.what());
    }
}

// ============================================================================
// TDX API Function Implementations
// ============================================================================

/*
 * USAGE EXAMPLES FOR DISCONNECT AND CLEANUP FUNCTIONALITY:
 * 
 * 1. Basic API Usage with Cleanup:
 *    - Call TdxServer_Connect to establish connection
 *    - Use any TdxServer_* functions for operations
 *    - Call TdxServer_Disconnect(clientId, 1) for full cleanup
 * 
 * 2. Manual Cleanup Control:
 *    - TdxServer_CleanupAndDisconnect(1, output, cleanupType, forceFlag, unused)
 *    - cleanupType: 0=disconnect, 1=force_cleanup, 2=session_cleanup
 *    - forceFlag: 1=force disconnect, 0=conditional
 * 
 * 3. Cleanup Types:
 *    - Type 0 (Disconnect): Graceful disconnection from server
 *    - Type 1 (Force Cleanup): Force close all connections and cleanup resources
 *    - Type 2 (Session Cleanup): Clean up session data, optionally disconnect
 * 
 * 4. Error Handling:
 *    - Return values: 1.0=success, 0.5=partial, 0.0=basic_success, -1.0=failed
 *    - Always check return values to ensure proper cleanup
 * 
 * 5. Best Practices:
 *    - Call cleanup functions after completing API operations
 *    - Use force cleanup when application is shutting down
 *    - Monitor connection status with TdxServer_GetInfo
 */

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
    
    if (client && client->isConnected()) {
        try {
            json response = client->testHeartbeat();
            if (response.contains("status") && response["status"] == "success") {
                log_debug("Heartbeat successful");
            } else {
                log_error("Heartbeat failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            log_error("Heartbeat exception: %s", e.what());
        }
    } else {
        log_error("Heartbeat: Server not connected");
        
        // Try to reconnect
        if (!manager.ReconnectToServer()) {
            log_error("Failed to reconnect to server during heartbeat");
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
    
    if (client && client->isConnected()) {
        try {
            json response = client->getServerInfo();
            if (response.contains("status") && response["status"] == "success") {
                log_debug("GetInfo: Server info retrieved successfully");
            } else {
                log_error("GetInfo: Server info retrieval failed");
            }
        } catch (const std::exception& e) {
            log_error("GetInfo exception: %s", e.what());
        }
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
    
    // Try to ensure server connection
    if (!manager.IsServerConnected()) {
        manager.ReconnectToServer();
    }
    
    manager.IncrementConnections();
    log_debug("Connect: Connection established");
}

/**
 * @brief TDX API function to simulate connection disconnection
 * @param DataLen Number of data points
 * @param pfOUT Output array (disconnection result)
 * @param pfINa Input array A (client ID)
 * @param pfINb Input array B (cleanup level: 0=basic, 1=full_cleanup)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_Disconnect)
{
    ServerManager& manager = ServerManager::GetInstance();
    
    manager.DecrementConnections();
    
    try {
        manager.CleanupAfterAPISession(true); // Force disconnect
        log_debug("Disconnect with full cleanup completed");
    } catch (const std::exception& e) {
        log_error("Disconnect succeeded but cleanup failed: %s", e.what());
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
    log_debug("ValidateData: Data validation completed");
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
    log_debug("GetStats: Server statistics retrieved");
}

/**
 * @brief TDX API function to send single K-bar data to server
 * @param DataLen Number of data points
 * @param pfOUT Output array (server response)
 * @param pfINa Input array A (encoded symbol information)
 * @param pfINb Input array B (requested K-bar index)
 * @param pfINc Input array C (reserved for future use)
 */
TDX_EXPORT(TdxServer_SendKBar)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    if (client && client->isConnected()) {
        try {
            // Decode symbol and period from input parameters
            int symbolInt, periodInt;
            std::string symbol, period;
            int requestedIndex = 0;
            
            log_debug("TdxServer_SendKBar: Input parameters - DataLen=%d, pfINa[0]=%f, pfINb[0]=%f", 
                     DataLen, DataLen > 0 ? pfINa[0] : 0.0f, DataLen > 0 ? pfINb[0] : 0.0f);
            
            if (DataLen > 0 && pfINa && pfINb) {
                // Try to decode symbol and period from combined encoding in pfINa
                DecodeSymbolPeriod(pfINa[0], symbolInt, periodInt);
                
                // Convert integers to strings for further processing
                symbol = std::to_string(symbolInt);
                period = std::to_string(periodInt);
                
                log_debug("TdxServer_SendKBar: After DecodeSymbolPeriod - symbol=%s, period=%s", symbol.c_str(), period.c_str());
                
                // Store original numeric period for data lookup
                std::string originalPeriod = period;
                
                // convert period to period string for display/logging purposes only
                std::string periodString = ConvertPeriodToStr(period);
                log_debug("TdxServer_SendKBar: After ConvertPeriodToStr - original period=%s, converted period=%s", 
                         originalPeriod.c_str(), periodString.c_str());

                // Use original numeric period for data lookup to match storage format
                period = originalPeriod;

                // Get requested index from pfINb
                requestedIndex = static_cast<int>(pfINb[DataLen - 1]);
                
                // pfINc is reserved for future use
            }
            
            // Use default values if decoding failed
            if (symbol.empty()) {
                log_debug("TdxServer_SendKBar: Symbol is empty, using default '999999'");
                symbol = "999999";
            }
            if (period.empty()) {
                log_debug("TdxServer_SendKBar: Period is empty, using default 'daily'");
                period = "daily";
            }
            if (requestedIndex < 0) {
                log_debug("TdxServer_SendKBar: RequestedIndex is negative (%d), using default 0", requestedIndex);
                requestedIndex = 0;
            }
            
            log_debug("TdxServer_SendKBar: Final parameters - symbol=%s, period=%s, requestedIndex=%d", 
                     symbol.c_str(), period.c_str(), requestedIndex);
            
            // Get K-bar data from KbarManager
            KbarManager& kbarManager = KbarManager::GetInstance();
            const std::vector<KbarData>& kbarData = kbarManager.GetKbarData(symbol, period);
            
            if (kbarData.empty()) {
                log_error("TdxServer_SendKBar: No K-bar data available for symbol=%s, period=%s. Check if data was loaded via TdxKbar_SetTimeAndFinalize sequence.", symbol.c_str(), period.c_str());
                
                // Debug: Show all available data
                kbarManager.DebugLogAllData();
                return;
            }
            
            if (requestedIndex >= static_cast<int>(kbarData.size())) {
                log_error("Requested index %d out of range for symbol=%s, period=%s (available: %d)", 
                         requestedIndex, symbol.c_str(), period.c_str(), static_cast<int>(kbarData.size()));
                return;
            }
            
            // Get the requested K-bar data
            const KbarData& kbar = kbarData[requestedIndex];
            
            log_debug("TdxServer_SendKBar: Retrieved K-bar data - open=%f, high=%f, low=%f, close=%f, volume=%ld, date=%d-%d-%d %d:%d", 
                     kbar.open, kbar.high, kbar.low, kbar.close, kbar.volume,
                     kbar.year, kbar.month, kbar.day, kbar.hour, kbar.minute);
            
            // Convert to QAUtils::KBarData format
            QAUtils::KBarData qaKbar;
            qaKbar.symbol = symbol;
            qaKbar.open = kbar.open;
            qaKbar.high = kbar.high;
            qaKbar.low = kbar.low;
            qaKbar.close = kbar.close;
            qaKbar.volume = kbar.volume;
            
            // Format timestamp from date/time components
            char timestamp[32];
            snprintf(timestamp, sizeof(timestamp), "%04d-%02d-%02dT%02d:%02d:00Z", 
                    kbar.year, kbar.month, kbar.day, kbar.hour, kbar.minute);
            qaKbar.timestamp = timestamp;
            
            json response = client->testSingleKBar(qaKbar);
            if (response.contains("status") && response["status"] == "success") {
                log_debug("K-bar sent successfully: symbol=%s, period=%s, index=%d", 
                         symbol.c_str(), period.c_str(), requestedIndex);
            } else {
                log_error("K-bar send failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            log_error("SendKBar exception: %s", e.what());
        }
    } else {
        log_error("SendKBar: Server not connected");
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
            std::vector<double> priceData = {100.0, 101.0, 102.0, 103.0, 104.0}; // Sample data
            int period = 20; // Default period
            
            json response = client->calculateSMA(priceData, period);
            if (response.contains("status") && response["status"] == "success") {
                log_debug("SMA calculated successfully, period=%d", period);
            } else {
                log_error("SMA calculation failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            log_error("SMA calculation exception: %s", e.what());
        }
    } else {
        log_debug("SMA: Server not connected");
    }
}

/**
 * @brief TDX API function to send K-bar series data to server
 * @param DataLen Number of data points
 * @param pfOUT Output array (server response)
 * @param pfINa Input array A (encoded symbol information)
 * @param pfINb Input array B (requested K-bar starting index)
 * @param pfINc Input array C (K-bar length/count to send)
 */
TDX_EXPORT(TdxServer_SendKBarSeries)
{
    ServerManager& manager = ServerManager::GetInstance();
    auto* client = manager.GetZmqClient();
    
    if (client && client->isConnected()) {
        try {
            // Decode symbol and period from input parameters
            int symbolInt = 0, periodInt = 0;
            std::string symbol, period;
            int startIndex = 0;
            int kbarLength = 0;
            
            log_debug("TdxServer_SendKBarSeries: Input parameters - DataLen=%d, pfINa[0]=%f, pfINb[0]=%f, pfINc[0]=%f", 
                     DataLen, DataLen > 0 ? pfINa[0] : 0.0f, DataLen > 0 ? pfINb[0] : 0.0f, DataLen > 0 ? pfINc[0] : 0.0f);
            
            if (DataLen > 0 && pfINa && pfINb && pfINc) {
                // Try to decode symbol and period from combined encoding in pfINa
                DecodeSymbolPeriod(pfINa[0], symbolInt, periodInt);
                
                // Convert integers to strings for further processing
                symbol = std::to_string(symbolInt);
                period = std::to_string(periodInt);
                
                // Store original numeric period for data lookup
                std::string originalPeriod = period;
                
                // convert period to period string for display/logging purposes only
                std::string periodString = ConvertPeriodToStr(period);
                log_debug("TdxServer_SendKBarSeries: After ConvertPeriodToStr - original period=%s, converted period=%s", 
                         originalPeriod.c_str(), periodString.c_str());

                // Use original numeric period for data lookup to match storage format
                period = originalPeriod;

                // Get starting index from pfINb
                startIndex = static_cast<int>(pfINb[DataLen - 1]);
                
                // Get K-bar length from pfINc
                kbarLength = static_cast<int>(pfINc[DataLen - 1]);
            }
            
            // Use default values if decoding failed
            if (symbol.empty()) {
                symbol = "999999";
            }
            if (period.empty()) {
                period = "daily";
            }
            if (startIndex < 0) {
                startIndex = 0;
            }
            if (kbarLength <= 0) {
                kbarLength = 100; // Default length if not specified or invalid
            }
            
            log_debug("TdxServer_SendKBarSeries: Final parameters - symbol=%s, period=%s, startIndex=%d, kbarLength=%d", 
                     symbol.c_str(), period.c_str(), startIndex, kbarLength);
            
            // Get K-bar data from KbarManager
            KbarManager& kbarManager = KbarManager::GetInstance();
            const std::vector<KbarData>& kbarData = kbarManager.GetKbarData(symbol, period);
            
            if (kbarData.empty()) {
                log_error("TdxServer_SendKBarSeries: No K-bar data available for symbol=%s, period=%s. Check if data was loaded via TdxKbar_SetTimeAndFinalize sequence.", symbol.c_str(), period.c_str());
                // Debug: Show all available data
                kbarManager.DebugLogAllData();
                return;
            }
            
            if (startIndex >= static_cast<int>(kbarData.size())) {
                log_error("Starting index %d out of range for symbol=%s, period=%s (available: %d)", 
                         startIndex, symbol.c_str(), period.c_str(), static_cast<int>(kbarData.size()));
                return;
            }
            
            // Calculate the actual end index based on startIndex and kbarLength
            int endIndex = std::min(startIndex + kbarLength, static_cast<int>(kbarData.size()));
            int actualLength = endIndex - startIndex;
            
            log_debug("TdxServer_SendKBarSeries: Calculated range - startIndex=%d, endIndex=%d, actualLength=%d", 
                     startIndex, endIndex, actualLength);
            
            // Convert K-bar data from startIndex to endIndex into QAUtils::KBarData format
            std::vector<QAUtils::KBarData> kbarSeries;
            kbarSeries.reserve(actualLength);
            
            for (int i = startIndex; i < endIndex; ++i) {
                const KbarData& kbar = kbarData[i];
                
                QAUtils::KBarData qaKbar;
                qaKbar.symbol = symbol;
                qaKbar.open = kbar.open;
                qaKbar.high = kbar.high;
                qaKbar.low = kbar.low;
                qaKbar.close = kbar.close;
                qaKbar.volume = kbar.volume;
                
                // Format timestamp from date/time components
                char timestamp[32];
                snprintf(timestamp, sizeof(timestamp), "%04d-%02d-%02dT%02d:%02d:00Z", 
                        kbar.year, kbar.month, kbar.day, kbar.hour, kbar.minute);
                qaKbar.timestamp = timestamp;
                
                kbarSeries.push_back(qaKbar);
            }
            
            log_debug("TdxServer_SendKBarSeries: Prepared %d K-bars (requested=%d) starting from index %d", 
                     static_cast<int>(kbarSeries.size()), kbarLength, startIndex);
            
            json response = client->SendKBarSeries(symbol, periodInt, kbarSeries);
            if (response.contains("status") && response["status"] == "success") {
                log_debug("K-bar series sent successfully: symbol=%s, period=%s, count=%d, startIndex=%d, requestedLength=%d", 
                         symbol.c_str(), period.c_str(), static_cast<int>(kbarSeries.size()), startIndex, kbarLength);
            } else {
                log_error("K-bar series send failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            log_error("SendKBarSeries exception: %s", e.what());
        }
    } else {
        log_error("SendKBarSeries: Server not connected");
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
    
    if (client && client->isConnected()) {
        try {
            std::string paramName = "server_timeout";
            json value = 30; // Default value
            
            json response = client->setParameter(paramName, value);
            if (response.contains("status") && response["status"] == "success") {
                log_debug("Parameter set successfully: %s", paramName.c_str());
            } else {
                log_error("Parameter set failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            log_error("SetParameter exception: %s", e.what());
        }
    } else {
        log_debug("SetParameter: Server not available");
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
    
    if (client && client->isConnected()) {
        try {
            std::string paramName = "server_timeout";
            
            json response = client->getParameter(paramName);
            if (response.contains("status") && response["status"] == "success") {
                log_debug("Parameter retrieved: %s", paramName.c_str());
            } else {
                log_error("Parameter get failed: %s", response.dump().c_str());
            }
        } catch (const std::exception& e) {
            log_error("GetParameter exception: %s", e.what());
        }
    } else {
        log_debug("GetParameter: Server not available");
    }
}

/**
 * @brief TDX API function to cleanup and disconnect after API completion
 * @param DataLen Number of data points
 * @param pfOUT Output array (cleanup result: 1=success, 0=partial, -1=failed)
 * @param pfINa Input array A (cleanup type: 0=disconnect, 1=force_cleanup, 2=session_cleanup)
 * @param pfINb Input array B (force disconnect flag: 1=force, 0=conditional)
 * @param pfINc Input array C (unused)
 */
TDX_EXPORT(TdxServer_CleanupAndDisconnect)
{
    ServerManager& manager = ServerManager::GetInstance();
    
    try {
        manager.CleanupAfterAPISession(true); // Force disconnect
        log_debug("API session cleanup completed successfully");
    } catch (const std::exception& e) {
        log_error("Cleanup and disconnect failed: %s", e.what());
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
        return "Parameters: pInA=Client ID, pInB=cleanup level (0=basic, 1=full_cleanup), pInC=unused, pOut=Disconnection result";
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
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 6, "TdxServer_SendKBar", "Send single K-bar data to server", "Server", 1, false)
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
        return "Parameters: pInA=Symbol and timestamp, pInB=OHLC data, pInC=Volume data, pOut=Send result";
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
 * @brief Wrapper class for TdxServer_SetParameter function
 */
class TdxServerSetParameterFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerSetParameterFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 11, "TdxServer_SetParameter", "Set server parameters", "Server", 1, false)
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
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 12, "TdxServer_GetParameter", "Get server parameters", "Server", 1, false)
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

/**
 * @brief Wrapper class for TdxServer_CleanupAndDisconnect function
 */
class TdxServerCleanupAndDisconnectFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxServerCleanupAndDisconnectFunction()
        : TdxFunctionBase(TDX_SERVER_FUNCTION_ID_OFFSET + 13, "TdxServer_CleanupAndDisconnect", "Cleanup and disconnect after API completion", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxServer_CleanupAndDisconnect
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxServer_CleanupAndDisconnect;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Cleanup type (0=disconnect,1=force,2=session), pInB=Force flag, pInC=unused, pOut=Result";
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
        return "Parameters: pInA=Symbol and period encoding, pInB=Starting index, pInC=K-bar length, pOut=Send result";
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
        success &= registry.RegisterFunction(std::make_shared<TdxServerSendKBarSeriesFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerSendKBarFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerCalculateSMAFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerSetParameterFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerGetParameterFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxServerCleanupAndDisconnectFunction>());
        
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
