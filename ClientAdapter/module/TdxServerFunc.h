#pragma once

#include "TdxFunctionBase.h"
#include <string>
#include <memory>
#include <ctime>

// Forward declarations
namespace QAUtils {
    class ZmqClient;
}

/**
 * @brief Server status information structure
 */
struct ServerStatus
{
    bool isRunning;          ///< Server running status
    int connectionCount;     ///< Number of active connections
    std::time_t startTime;   ///< Server start time
    std::string version;     ///< Server version string
    double uptime;           ///< Server uptime in seconds
    
    /**
     * @brief Default constructor for ServerStatus
     */
    ServerStatus();
    
    /**
     * @brief Constructor with parameters
     * @param running Server running status
     * @param connections Number of connections
     * @param start Start time
     * @param ver Version string
     */
    ServerStatus(bool running, int connections, std::time_t start, const std::string& ver);
};

/**
 * @brief Server manager singleton class for managing server state
 */
class ServerManager
{
private:
    static std::unique_ptr<ServerManager> s_instance;
    ServerStatus m_status;
    std::time_t m_startTime;
    std::unique_ptr<QAUtils::ZmqClient> m_zmqClient;
    
    /**
     * @brief Private constructor for singleton
     */
    ServerManager();

public:
    /**
     * @brief Destructor for ServerManager
     */
    ~ServerManager();

    /**
     * @brief Get singleton instance
     * @return Reference to ServerManager instance
     */
    static ServerManager& GetInstance();
    
    /**
     * @brief Cleanup and destroy the singleton instance
     * 
     * This method should be called during plugin cleanup to ensure
     * the ServerManager destructor is called and resources are properly cleaned up.
     */
    static void Cleanup();
    
    /**
     * @brief Get current server status
     * @return Current ServerStatus object
     */
    const ServerStatus& GetStatus() const;
    
    /**
     * @brief Update server status
     * @param status New server status
     */
    void UpdateStatus(const ServerStatus& status);
    
    /**
     * @brief Increment connection count
     */
    void IncrementConnections();
    
    /**
     * @brief Decrement connection count
     */
    void DecrementConnections();
    
    /**
     * @brief Get server uptime in seconds
     * @return Uptime in seconds
     */
    double GetUptime() const;
    
    /**
     * @brief Reset server statistics
     */
    void Reset();

    /**
     * @brief Get ZMQ client instance
     * @return Pointer to ZMQ client or nullptr if not available
     */
    QAUtils::ZmqClient* GetZmqClient();

    /**
     * @brief Check if server is connected
     * @return true if ZMQ client is connected to QuantServer
     */
    bool IsServerConnected() const;

    /**
     * @brief Reconnect to server if disconnected
     * @return true if connection successful
     */
    bool ReconnectToServer();

    /**
     * @brief Disconnect ZMQ client after API operations complete
     * 
     * This method provides controlled disconnection after API completion
     * without destroying the entire ServerManager instance.
     */
    void DisconnectAfterAPI();

    /**
     * @brief Cleanup resources after API session completion
     * 
     * This method should be called when an API session is complete to ensure
     * proper resource cleanup while keeping the ServerManager instance alive.
     * @param forceDisconnect If true, forces disconnection even if connection is healthy
     */
    void CleanupAfterAPISession(bool forceDisconnect = false);
};

// TDX API Function declarations
extern "C" {
    /**
     * @brief TDX API function for server heartbeat/ping
     * @param DataLen Number of data points
     * @param pfOUT Output array (heartbeat response)
     * @param pfINa Input array A (client timestamp)
     * @param pfINb Input array B (unused)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_Heartbeat(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);
    
    /**
     * @brief TDX API function to get server information
     * @param DataLen Number of data points
     * @param pfOUT Output array (server info encoded)
     * @param pfINa Input array A (info type: 0=status, 1=version, 2=uptime, 3=connections)
     * @param pfINb Input array B (unused)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_GetInfo(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);
    
    /**
     * @brief TDX API function to simulate connection establishment
     * @param DataLen Number of data points
     * @param pfOUT Output array (connection result)
     * @param pfINa Input array A (client ID)
     * @param pfINb Input array B (connection timeout)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_Connect(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);
    
    /**
     * @brief TDX API function to simulate connection disconnection
     * @param DataLen Number of data points
     * @param pfOUT Output array (disconnection result)
     * @param pfINa Input array A (client ID)
     * @param pfINb Input array B (cleanup level: 0=basic, 1=full_cleanup)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_Disconnect(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);
    
    /**
     * @brief TDX API function to validate data integrity
     * @param DataLen Number of data points
     * @param pfOUT Output array (validation result)
     * @param pfINa Input array A (data to validate)
     * @param pfINb Input array B (expected checksum)
     * @param pfINc Input array C (validation type)
     */
    void TdxServer_ValidateData(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);
    
    /**
     * @brief TDX API function to get server statistics
     * @param DataLen Number of data points
     * @param pfOUT Output array (statistics data)
     * @param pfINa Input array A (stat type: 0=memory, 1=cpu, 2=network, 3=storage)
     * @param pfINb Input array B (time window in seconds)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_GetStats(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);

    /**
     * @brief TDX API function to send single K-bar data to server
     * @param DataLen Number of data points
     * @param pfOUT Output array (server response)
     * @param pfINa Input array A (encoded symbol and timestamp)
     * @param pfINb Input array B (OHLC data packed: open*10000 + high)
     * @param pfINc Input array C (OHLC data packed: low*10000 + close, volume in high 16 bits)
     */
    void TdxServer_SendKBar(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);

    /**
     * @brief TDX API function to calculate Simple Moving Average
     * @param DataLen Number of data points
     * @param pfOUT Output array (SMA values)
     * @param pfINa Input array A (price data)
     * @param pfINb Input array B (period)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_CalculateSMA(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);

    /**
     * @brief TDX API function to calculate RSI (Relative Strength Index)
     * @param DataLen Number of data points
     * @param pfOUT Output array (RSI values)
     * @param pfINa Input array A (price data)
     * @param pfINb Input array B (period)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_CalculateRSI(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);

    /**
     * @brief TDX API function to calculate Bollinger Bands
     * @param DataLen Number of data points
     * @param pfOUT Output array (encoded Bollinger Bands data)
     * @param pfINa Input array A (price data)
     * @param pfINb Input array B (period)
     * @param pfINc Input array C (standard deviation multiplier * 100)
     */
    void TdxServer_CalculateBollinger(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);

    /**
     * @brief TDX API function to send K-bar series data to server
     * @param DataLen Number of data points
     * @param pfOUT Output array (server response)
     * @param pfINa Input array A (price data - close prices)
     * @param pfINb Input array B (volume data)
     * @param pfINc Input array C (symbol encoding)
     */
    void TdxServer_SendKBarSeries(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);

    /**
     * @brief TDX API function to calculate EMA (Exponential Moving Average)
     * @param DataLen Number of data points
     * @param pfOUT Output array (EMA values)
     * @param pfINa Input array A (price data)
     * @param pfINb Input array B (period)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_CalculateEMA(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);

    /**
     * @brief TDX API function to set server parameters
     * @param DataLen Number of data points
     * @param pfOUT Output array (operation result)
     * @param pfINa Input array A (parameter type encoded)
     * @param pfINb Input array B (parameter value)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_SetParameter(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);

    /**
     * @brief TDX API function to get server parameters
     * @param DataLen Number of data points
     * @param pfOUT Output array (parameter values)
     * @param pfINa Input array A (parameter type encoded)
     * @param pfINb Input array B (unused)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_GetParameter(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);

    /**
     * @brief TDX API function to cleanup and disconnect after API completion
     * @param DataLen Number of data points
     * @param pfOUT Output array (cleanup result: 1=success, 0=partial, -1=failed)
     * @param pfINa Input array A (cleanup type: 0=disconnect, 1=force_cleanup, 2=session_cleanup)
     * @param pfINb Input array B (force disconnect flag: 1=force, 0=conditional)
     * @param pfINc Input array C (unused)
     */
    void TdxServer_CleanupAndDisconnect(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc);
}

/**
 * @brief Register all TDX server functions with the function registry
 * @return true if all functions were registered successfully
 */
bool RegisterTdxServerFunctions();
