#pragma once

#include "TdxFunctionBase.h"
#include <string>
#include <memory>
#include <ctime>

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
    
    /**
     * @brief Private constructor for singleton
     */
    ServerManager();

public:
    /**
     * @brief Get singleton instance
     * @return Reference to ServerManager instance
     */
    static ServerManager& GetInstance();
    
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
     * @param pfINb Input array B (unused)
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
}

/**
 * @brief Register all TDX server functions with the function registry
 * @return true if all functions were registered successfully
 */
bool RegisterTdxServerFunctions();
