#include "TdxServerFunc.h"
#include "../core/TdxFunctionRegistry.h"
#include "../utils/log.h"
#include <cstring>
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <cmath>

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
    : m_startTime(std::time(nullptr))
{
    m_status = ServerStatus(true, 0, m_startTime, "TDX-Server-1.0.0");
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
    std::time_t serverTime = std::time(nullptr);
    
    for (int i = 0; i < DataLen; i++)
    {
        float clientTimestamp = pfINa[i];
        float responseTime = static_cast<float>(serverTime);
        
        // Calculate round-trip time estimate
        float rtt = responseTime - clientTimestamp;
        
        // Return server timestamp + RTT as response
        pfOUT[i] = responseTime + (rtt * 0.5f);
        
        log_debug("Heartbeat: Client=%f, Server=%f, RTT=%f", 
                 clientTimestamp, responseTime, rtt);
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
    const ServerStatus& status = manager.GetStatus();
    
    for (int i = 0; i < DataLen; i++)
    {
        int infoType = static_cast<int>(pfINa[i]);
        
        switch (infoType)
        {
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
