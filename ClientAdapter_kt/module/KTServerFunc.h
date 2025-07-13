#pragma once

#ifdef ENABLE_SERVER_FUNCTIONS

#include "../core/KTFunctionBase.h"
#include <string>
#include <memory>
#include <ctime>

// Forward declarations
namespace QAUtils {
    class KTZmqClient;
}

/**
 * @brief Server status information structure for KT platform
 */
struct KTServerStatus
{
    bool isRunning;          ///< Server running status
    int connectionCount;     ///< Number of active connections
    std::time_t startTime;   ///< Server start time
    std::string version;     ///< Server version string
    double uptime;           ///< Server uptime in seconds
    
    /**
     * @brief Default constructor for KTServerStatus
     */
    KTServerStatus();
    
    /**
     * @brief Constructor with parameters
     * @param running Server running status
     * @param connections Number of connections
     * @param start Start time
     * @param ver Version string
     */
    KTServerStatus(bool running, int connections, std::time_t start, const std::string& ver);
};

/**
 * @brief Server manager singleton class for managing server state in KT platform
 */
class KTServerManager
{
private:
    static std::unique_ptr<KTServerManager> s_instance;
    KTServerStatus m_status;
    std::time_t m_startTime;
    std::unique_ptr<QAUtils::KTZmqClient> m_zmqClient;
    
    /**
     * @brief Private constructor for singleton
     */
    KTServerManager();

public:
    /**
     * @brief Destructor for KTServerManager
     */
    ~KTServerManager();

    /**
     * @brief Get singleton instance
     * @return Reference to KTServerManager instance
     */
    static KTServerManager& GetInstance();
    
    /**
     * @brief Cleanup and destroy the singleton instance
     * 
     * This method should be called during plugin cleanup to ensure
     * the KTServerManager destructor is called and resources are properly cleaned up.
     */
    static void Cleanup();
    
    /**
     * @brief Get current server status
     * @return Current KTServerStatus object
     */
    const KTServerStatus& GetStatus() const;
    
    /**
     * @brief Update server status
     * @param status New server status
     */
    void UpdateStatus(const KTServerStatus& status);
    
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
    QAUtils::KTZmqClient* GetZmqClient();

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
     * without destroying the entire KTServerManager instance.
     */
    void DisconnectAfterAPI();

    /**
     * @brief Cleanup resources after API session completion
     * 
     * This method should be called when an API session is complete to ensure
     * proper resource cleanup while keeping the KTServerManager instance alive.
     * @param forceDisconnect If true, forces disconnection even if connection is healthy
     */
    void CleanupAfterAPISession(bool forceDisconnect = false);
};

// KT API Function declarations
extern "C" {
    /**
     * @brief KT API function for server heartbeat/ping
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_Heartbeat(CALCINFO* pCalcInfo);
    
    /**
     * @brief KT API function to get server information
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_GetInfo(CALCINFO* pCalcInfo);
    
    /**
     * @brief KT API function to simulate connection establishment
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_Connect(CALCINFO* pCalcInfo);
    
    /**
     * @brief KT API function to simulate connection disconnection
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_Disconnect(CALCINFO* pCalcInfo);
    
    /**
     * @brief KT API function to validate data integrity
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_ValidateData(CALCINFO* pCalcInfo);
    
    /**
     * @brief KT API function to get server statistics
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_GetStats(CALCINFO* pCalcInfo);

    /**
     * @brief KT API function to send single K-bar data to server
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_SendKBar(CALCINFO* pCalcInfo);

    /**
     * @brief KT API function to calculate Simple Moving Average
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_CalculateSMA(CALCINFO* pCalcInfo);

    /**
     * @brief KT API function to send K-bar series data to server
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_SendKBarSeries(CALCINFO* pCalcInfo);

    /**
     * @brief KT API function to set server parameters
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_SetParameter(CALCINFO* pCalcInfo);

    /**
     * @brief KT API function to get server parameters
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_GetParameter(CALCINFO* pCalcInfo);

    /**
     * @brief KT API function to cleanup and disconnect after API completion
     * @param pCalcInfo Calculation information structure
     * @return BOOL TRUE if successful, FALSE otherwise
     */
    BOOL KTServer_CleanupAndDisconnect(CALCINFO* pCalcInfo);
}

/**
 * @brief Register all KT server functions with the function registry
 * @return true if all functions were registered successfully
 */
bool RegisterKTServerFunctions();

#endif // ENABLE_SERVER_FUNCTIONS