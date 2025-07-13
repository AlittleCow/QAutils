#ifdef ENABLE_SERVER_FUNCTIONS

#include "KTServerFunc.h"
#include "KTCommonFunc.h"
#include "../core/KTFunctionRegistry.h"
#include "../utils/log.h"
#include "KTServerApi.h"
#include <cstring>
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <thread>
#include <chrono>

// KT Server Function ID offset (starting after common functions)
constexpr int KT_SERVER_FUNCTION_ID_OFFSET = 3000;

// Static member initialization
std::unique_ptr<KTServerManager> KTServerManager::s_instance = nullptr;

// ============================================================================
// KTServerStatus Implementation
// ============================================================================

/**
 * @brief Default constructor for KTServerStatus
 */
KTServerStatus::KTServerStatus()
    : isRunning(false), connectionCount(0), startTime(0), version("Unknown"), uptime(0.0)
{
}

/**
 * @brief Constructor with parameters
 */
KTServerStatus::KTServerStatus(bool running, int connections, std::time_t start, const std::string& ver)
    : isRunning(running), connectionCount(connections), startTime(start), version(ver)
{
    uptime = std::difftime(std::time(nullptr), startTime);
}

// ============================================================================
// KTServerManager Implementation
// ============================================================================

/**
 * @brief Private constructor for singleton
 */
KTServerManager::KTServerManager()
    : m_startTime(std::time(nullptr)), m_zmqClient(nullptr)
{
    m_status = KTServerStatus(true, 0, m_startTime, "KT-Server-1.0.0");
    
    // Initialize ZMQ client for server communication
    try {
        m_zmqClient = std::make_unique<QAUtils::KTZmqClient>("localhost", 5555);
        if (m_zmqClient->connect()) {
            log_debug("KTServerManager: Successfully connected to QuantServer");
        } else {
            log_warn("KTServerManager: Failed to connect to QuantServer on startup");
        }
    } catch (const std::exception& e) {
        log_error("KTServerManager: Exception during ZMQ client initialization: %s", e.what());
        m_zmqClient = nullptr;
    }
    
    log_debug("KTServerManager initialized with start time: %ld", m_startTime);
}

/**
 * @brief Destructor for KTServerManager
 */
KTServerManager::~KTServerManager()
{
    log_debug("KTServerManager destructor called");
    log_debug("Checking ZMQ client state in destructor");
    
    if (m_zmqClient && m_zmqClient->isConnected()) {
        log_debug("Disconnecting ZMQ client");
        m_zmqClient->disconnect();
        log_debug("ZMQ client disconnected");
    } else if (m_zmqClient) {
        log_debug("ZMQ client already disconnected, skipping disconnect in destructor");
    } else {
        log_debug("No ZMQ client to disconnect");
    }
    
    // Force close ZMQ context to prevent hanging during DLL unload
    if (m_zmqClient) {
        log_debug("Force closing ZMQ context");
        m_zmqClient->forceCloseContext();
        m_zmqClient.reset();
        log_debug("ZMQ client reset completed");
    }
    
    log_debug("KTServerManager destructor completed");
}

/**
 * @brief Get singleton instance
 */
KTServerManager& KTServerManager::GetInstance()
{
    if (!s_instance) {
        s_instance = std::unique_ptr<KTServerManager>(new KTServerManager());
        log_debug("KTServerManager singleton instance created");
    }
    return *s_instance;
}

/**
 * @brief Cleanup and destroy the singleton instance
 */
void KTServerManager::Cleanup()
{
    if (s_instance) {
        log_debug("Cleaning up KTServerManager singleton instance");
        s_instance.reset();
        log_debug("KTServerManager singleton instance cleaned up");
    } else {
        log_debug("KTServerManager singleton instance already cleaned up or never created");
    }
}

/**
 * @brief Get current server status
 */
const KTServerStatus& KTServerManager::GetStatus() const
{
    // Update uptime before returning
    const_cast<KTServerStatus&>(m_status).uptime = GetUptime();
    return m_status;
}

/**
 * @brief Update server status
 */
void KTServerManager::UpdateStatus(const KTServerStatus& status)
{
    m_status = status;
    log_debug("Server status updated: running=%s, connections=%d", 
              status.isRunning ? "true" : "false", status.connectionCount);
}

/**
 * @brief Increment connection count
 */
void KTServerManager::IncrementConnections()
{
    m_status.connectionCount++;
    log_debug("Connection count incremented to: %d", m_status.connectionCount);
}

/**
 * @brief Decrement connection count
 */
void KTServerManager::DecrementConnections()
{
    if (m_status.connectionCount > 0)
    {
        m_status.connectionCount--;
    }
    log_debug("Connection count decremented to: %d", m_status.connectionCount);
}

/**
 * @brief Get server uptime in seconds
 */
double KTServerManager::GetUptime() const
{
    return std::difftime(std::time(nullptr), m_startTime);
}

/**
 * @brief Reset server statistics
 */
void KTServerManager::Reset()
{
    m_startTime = std::time(nullptr);
    m_status = KTServerStatus(true, 0, m_startTime, "KT-Server-1.0.0");
    log_debug("Server statistics reset");
}

/**
 * @brief Get ZMQ client instance
 */
QAUtils::KTZmqClient* KTServerManager::GetZmqClient()
{
    return m_zmqClient.get();
}

/**
 * @brief Check if server is connected
 */
bool KTServerManager::IsServerConnected() const
{
    return m_zmqClient && m_zmqClient->isConnected();
}

/**
 * @brief Reconnect to server if disconnected
 */
bool KTServerManager::ReconnectToServer()
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
        log_error("No ZMQ client available for reconnection");
        return false;
    }
}

/**
 * @brief Disconnect ZMQ client after API operations complete
 */
void KTServerManager::DisconnectAfterAPI()
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
 */
void KTServerManager::CleanupAfterAPISession(bool forceDisconnect)
{
    try {
        if (forceDisconnect || !IsServerConnected()) {
            DisconnectAfterAPI();
        }
        
        // Reset any temporary state that might accumulate during API usage
        // Keep core statistics but clear temporary data
        log_debug("API session cleanup completed, forceDisconnect=%s", forceDisconnect ? "true" : "false");
    } catch (const std::exception& e) {
        log_error("Exception during API session cleanup: %s", e.what());
    }
}

// ============================================================================
// KT Server Function Classes
// ============================================================================

/**
 * @brief KT Server Heartbeat Function
 */
class KTServerHeartbeatFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTServerHeartbeatFunction()
        : KTFunctionBase(KT_SERVER_FUNCTION_ID_OFFSET + 0, "KTServer_Heartbeat", "Server heartbeat/ping function", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for KTServer_Heartbeat
     */
    pKTFUNC GetKTFunctionPointer() const override
    {
        return reinterpret_cast<pKTFUNC>(KTServer_Heartbeat);
    }
};

/**
 * @brief KT Server Get Info Function
 */
class KTServerGetInfoFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTServerGetInfoFunction()
        : KTFunctionBase(KT_SERVER_FUNCTION_ID_OFFSET + 1, "KTServer_GetInfo", "Get server information", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for KTServer_GetInfo
     */
    pKTFUNC GetKTFunctionPointer() const override
    {
        return reinterpret_cast<pKTFUNC>(KTServer_GetInfo);
    }
};

/**
 * @brief KT Server Connect Function
 */
class KTServerConnectFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTServerConnectFunction()
        : KTFunctionBase(KT_SERVER_FUNCTION_ID_OFFSET + 2, "KTServer_Connect", "Simulate client connection", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for KTServer_Connect
     */
    pKTFUNC GetKTFunctionPointer() const override
    {
        return reinterpret_cast<pKTFUNC>(KTServer_Connect);
    }
};

/**
 * @brief KT Server Disconnect Function
 */
class KTServerDisconnectFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTServerDisconnectFunction()
        : KTFunctionBase(KT_SERVER_FUNCTION_ID_OFFSET + 3, "KTServer_Disconnect", "Simulate client disconnection", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for KTServer_Disconnect
     */
    pKTFUNC GetKTFunctionPointer() const override
    {
        return reinterpret_cast<pKTFUNC>(KTServer_Disconnect);
    }
};

/**
 * @brief KT Server Get Stats Function
 */
class KTServerGetStatsFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTServerGetStatsFunction()
        : KTFunctionBase(KT_SERVER_FUNCTION_ID_OFFSET + 4, "KTServer_GetStats", "Get server statistics", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for KTServer_GetStats
     */
    pKTFUNC GetKTFunctionPointer() const override
    {
        return reinterpret_cast<pKTFUNC>(KTServer_GetStats);
    }
};

/**
 * @brief KT Server Send K-Bar Function
 */
class KTServerSendKBarFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTServerSendKBarFunction()
        : KTFunctionBase(KT_SERVER_FUNCTION_ID_OFFSET + 5, "KTServer_SendKBar", "Send single K-bar data to server", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for KTServer_SendKBar
     */
    pKTFUNC GetKTFunctionPointer() const override
    {
        return reinterpret_cast<pKTFUNC>(KTServer_SendKBar);
    }
};

/**
 * @brief KT Server Calculate SMA Function
 */
class KTServerCalculateSMAFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTServerCalculateSMAFunction()
        : KTFunctionBase(KT_SERVER_FUNCTION_ID_OFFSET + 6, "KTServer_CalculateSMA", "Calculate SMA using server", "Server", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for KTServer_CalculateSMA
     */
    pKTFUNC GetKTFunctionPointer() const override
    {
        return reinterpret_cast<pKTFUNC>(KTServer_CalculateSMA);
    }
};

// ============================================================================
// KT API Function Implementations
// ============================================================================

/**
 * @brief KT API function for server heartbeat/ping
 */
BOOL KTServer_Heartbeat(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_Heartbeat: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_Heartbeat called for symbol: %s", pCalcInfo->szLabel);
        
        KTServerManager& manager = KTServerManager::GetInstance();
        QAUtils::KTZmqClient* client = manager.GetZmqClient();
        
        if (!client) {
            log_error("KTServer_Heartbeat: No ZMQ client available");
            return FALSE;
        }
        
        if (!client->isConnected()) {
            log_debug("KTServer_Heartbeat: Client not connected, attempting to reconnect");
            if (!manager.ReconnectToServer()) {
                log_error("KTServer_Heartbeat: Failed to reconnect to server");
                return FALSE;
            }
        }
        
        // Send heartbeat request
        auto response = client->testHeartbeat();
        
        if (response.empty()) {
            log_error("KTServer_Heartbeat: Empty response from server");
            return FALSE;
        }
        
        // Set output data based on response
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            // Simple heartbeat response: 1.0 for success, 0.0 for failure
            float heartbeat_result = response.contains("status") && response["status"] == "ok" ? 1.0f : 0.0f;
            
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = heartbeat_result;
            }
        }
        
        log_debug("KTServer_Heartbeat completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_Heartbeat: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to get server information
 */
BOOL KTServer_GetInfo(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_GetInfo: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_GetInfo called for symbol: %s", pCalcInfo->szLabel);
        
        KTServerManager& manager = KTServerManager::GetInstance();
        const KTServerStatus& status = manager.GetStatus();
        
        // Set output data based on server status
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            // Encode server information into output array
            // Index 0: Server running status (1.0 = running, 0.0 = not running)
            // Index 1: Connection count
            // Index 2: Uptime in hours
            // Index 3: ZMQ connection status (1.0 = connected, 0.0 = disconnected)
            
            int idx = 0;
            if (idx < pCalcInfo->nCount) {
                pCalcInfo->ppResult[0][idx++] = status.isRunning ? 1.0f : 0.0f;
            }
            if (idx < pCalcInfo->nCount) {
                pCalcInfo->ppResult[0][idx++] = static_cast<float>(status.connectionCount);
            }
            if (idx < pCalcInfo->nCount) {
                pCalcInfo->ppResult[0][idx++] = static_cast<float>(status.uptime / 3600.0); // Convert to hours
            }
            if (idx < pCalcInfo->nCount) {
                pCalcInfo->ppResult[0][idx++] = manager.IsServerConnected() ? 1.0f : 0.0f;
            }
            
            // Fill remaining slots with the last value
            float lastValue = idx > 0 ? pCalcInfo->ppResult[0][idx-1] : 0.0f;
            for (int i = idx; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = lastValue;
            }
        }
        
        log_debug("KTServer_GetInfo completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_GetInfo: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to simulate connection establishment
 */
BOOL KTServer_Connect(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_Connect: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_Connect called for symbol: %s", pCalcInfo->szLabel);
        
        KTServerManager& manager = KTServerManager::GetInstance();
        
        // Attempt to connect or reconnect
        bool connected = manager.ReconnectToServer();
        
        if (connected) {
            manager.IncrementConnections();
            log_debug("KTServer_Connect: Connection established successfully");
        } else {
            log_error("KTServer_Connect: Failed to establish connection");
        }
        
        // Set output data
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            float connection_result = connected ? 1.0f : 0.0f;
            
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = connection_result;
            }
        }
        
        return connected ? TRUE : FALSE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_Connect: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to simulate connection disconnection
 */
BOOL KTServer_Disconnect(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_Disconnect: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_Disconnect called for symbol: %s", pCalcInfo->szLabel);
        
        KTServerManager& manager = KTServerManager::GetInstance();
        
        // Disconnect from server
        manager.DisconnectAfterAPI();
        manager.DecrementConnections();
        
        // Set output data
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            // Always return success for disconnect
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = 1.0f;
            }
        }
        
        log_debug("KTServer_Disconnect completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_Disconnect: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to validate data integrity
 */
BOOL KTServer_ValidateData(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_ValidateData: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_ValidateData called for symbol: %s", pCalcInfo->szLabel);
        
        // Simple data validation - check if result array is valid
         bool isValid = (pCalcInfo->ppResult != nullptr) && (pCalcInfo->ppResult[0] != nullptr) && (pCalcInfo->nCount > 0);
        
        // Set output data
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            float validation_result = isValid ? 1.0f : 0.0f;
            
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = validation_result;
            }
        }
        
        log_debug("KTServer_ValidateData completed: %s", isValid ? "valid" : "invalid");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_ValidateData: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to get server statistics
 */
BOOL KTServer_GetStats(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_GetStats: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_GetStats called for symbol: %s", pCalcInfo->szLabel);
        
        KTServerManager& manager = KTServerManager::GetInstance();
        const KTServerStatus& status = manager.GetStatus();
        
        // Set output data with various statistics
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            // Cycle through different statistics based on data length
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                switch (i % 4) {
                    case 0: // Connection count
                        pCalcInfo->ppResult[0][i] = static_cast<float>(status.connectionCount);
                        break;
                    case 1: // Uptime in minutes
                        pCalcInfo->ppResult[0][i] = static_cast<float>(status.uptime / 60.0);
                        break;
                    case 2: // Server running status
                        pCalcInfo->ppResult[0][i] = status.isRunning ? 1.0f : 0.0f;
                        break;
                    case 3: // ZMQ connection status
                        pCalcInfo->ppResult[0][i] = manager.IsServerConnected() ? 1.0f : 0.0f;
                        break;
                }
            }
        }
        
        log_debug("KTServer_GetStats completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_GetStats: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to send single K-bar data to server
 */
BOOL KTServer_SendKBar(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_SendKBar: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_SendKBar called for symbol: %s", pCalcInfo->szLabel);
        
        // This is a placeholder implementation
        // In a real implementation, you would extract K-bar data from pCalcInfo
        // and send it to the server using the ZMQ client
        
        // Set output data to indicate success
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = 1.0f; // Success indicator
            }
        }
        
        log_debug("KTServer_SendKBar completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_SendKBar: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to calculate Simple Moving Average
 */
BOOL KTServer_CalculateSMA(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_CalculateSMA: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_CalculateSMA called for symbol: %s", pCalcInfo->szLabel);
        
        // This is a placeholder implementation
        // In a real implementation, you would use the server's SMA calculation
        
        // Set output data to some calculated values
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = 100.0f + static_cast<float>(i); // Dummy SMA values
            }
        }
        
        log_debug("KTServer_CalculateSMA completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_CalculateSMA: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to send K-bar series data to server
 */
BOOL KTServer_SendKBarSeries(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_SendKBarSeries: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_SendKBarSeries called for symbol: %s", pCalcInfo->szLabel);
        
        // This is a placeholder implementation
        // In a real implementation, you would extract K-bar series data
        // and send it to the server
        
        // Set output data to indicate success
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = 1.0f; // Success indicator
            }
        }
        
        log_debug("KTServer_SendKBarSeries completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_SendKBarSeries: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to set server parameters
 */
BOOL KTServer_SetParameter(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_SetParameter: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_SetParameter called for symbol: %s", pCalcInfo->szLabel);
        
        // This is a placeholder implementation
        // In a real implementation, you would extract parameter information
        // and send it to the server
        
        // Set output data to indicate success
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = 1.0f; // Success indicator
            }
        }
        
        log_debug("KTServer_SetParameter completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_SetParameter: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to get server parameters
 */
BOOL KTServer_GetParameter(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_GetParameter: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_GetParameter called for symbol: %s", pCalcInfo->szLabel);
        
        // This is a placeholder implementation
        // In a real implementation, you would retrieve parameter values from the server
        
        // Set output data with dummy parameter values
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = 42.0f + static_cast<float>(i); // Dummy parameter values
            }
        }
        
        log_debug("KTServer_GetParameter completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_GetParameter: Exception: %s", e.what());
        return FALSE;
    }
}

/**
 * @brief KT API function to cleanup and disconnect after API completion
 */
BOOL KTServer_CleanupAndDisconnect(CALCINFO* pCalcInfo)
{
    if (!pCalcInfo) {
        log_error("KTServer_CleanupAndDisconnect: Invalid CALCINFO pointer");
        return FALSE;
    }

    try {
        log_debug("KTServer_CleanupAndDisconnect called for symbol: %s", pCalcInfo->szLabel);
        
        KTServerManager& manager = KTServerManager::GetInstance();
        
        // Perform cleanup and disconnect
        manager.CleanupAfterAPISession(true); // Force disconnect
        
        // Set output data to indicate cleanup result
        if (pCalcInfo->ppResult && pCalcInfo->ppResult[0] && pCalcInfo->nCount > 0) {
            for (int i = 0; i < pCalcInfo->nCount; i++) {
                pCalcInfo->ppResult[0][i] = 1.0f; // Success indicator
            }
        }
        
        log_debug("KTServer_CleanupAndDisconnect completed successfully");
        return TRUE;
        
    } catch (const std::exception& e) {
        log_error("KTServer_CleanupAndDisconnect: Exception: %s", e.what());
        return FALSE;
    }
}

// ============================================================================
// Function Registration
// ============================================================================

/**
 * @brief Register all KT server functions with the function registry
 */
bool RegisterKTServerFunctions()
{
    try {
        log_debug("Registering KT server functions...");
        
        KTFunctionRegistry& registry = KTFunctionRegistry::GetInstance();
        
        // Register server functions
        bool success = true;
        success &= registry.RegisterFunction(std::make_shared<KTServerHeartbeatFunction>());
        success &= registry.RegisterFunction(std::make_shared<KTServerGetInfoFunction>());
        success &= registry.RegisterFunction(std::make_shared<KTServerConnectFunction>());
        success &= registry.RegisterFunction(std::make_shared<KTServerDisconnectFunction>());
        success &= registry.RegisterFunction(std::make_shared<KTServerGetStatsFunction>());
        success &= registry.RegisterFunction(std::make_shared<KTServerSendKBarFunction>());
        success &= registry.RegisterFunction(std::make_shared<KTServerCalculateSMAFunction>());
        
        if (success) {
            log_debug("All KT server functions registered successfully");
        } else {
            log_error("Some KT server functions failed to register");
        }
        
        return success;
        
    } catch (const std::exception& e) {
        log_error("Failed to register KT server functions: %s", e.what());
        return false;
    }
}

#endif // ENABLE_SERVER_FUNCTIONS