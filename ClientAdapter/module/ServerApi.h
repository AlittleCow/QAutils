#pragma once

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <zmq.hpp>
#include <nlohmann/json.hpp>
#include "../utils/log.h"

using json = nlohmann::json;

namespace QAUtils {

/**
 * @brief Structure to represent K-bar data
 */
struct KBarData {
    std::string symbol;
    std::string timestamp;
    double open;
    double high;
    double low;
    double close;
    long volume;
};

/**
 * @brief Structure to represent API call request
 */
struct ApiRequest {
    std::string indicator_name;
    std::string indicator_function_name;
    json parameters;
    bool result_required;
};

/**
 * @brief ZMQ Client for communicating with QuantServer
 * 
 * This class provides a C++ interface to communicate with the Python QuantServer
 * using ZeroMQ messaging. It supports all the message types demonstrated in the
 * Python example client including heartbeat, kbar data, API calls, and control messages.
 */
class ZmqClient {
private:
    std::unique_ptr<zmq::context_t> context_;
    std::unique_ptr<zmq::socket_t> socket_;
    std::string server_host_;
    int server_port_;
    bool connected_;
    bool context_closed_;  ///< Flag to track if context has been force-closed

public:
    /**
     * @brief Construct a new ZmqClient object
     * 
     * @param server_host The hostname or IP address of the server (default: "localhost")
     * @param server_port The port number of the server (default: 5555)
     */
    ZmqClient(const std::string& server_host = "localhost", int server_port = 5555);

    /**
     * @brief Destroy the ZmqClient object and cleanup resources
     */
    ~ZmqClient();

    /**
     * @brief Connect to the QuantServer
     * 
     * @return true if connection successful, false otherwise
     */
    bool connect();

    /**
     * @brief Disconnect from the QuantServer
     */
    void disconnect();

    /**
     * @brief Check if client is connected to server
     * 
     * @return true if connected, false otherwise
     */
    bool isConnected() const;

    /**
     * @brief Validate connection health by checking socket state
     * 
     * @return true if connection is healthy, false otherwise
     */
    bool validateConnectionHealth();

    /**
     * @brief Emergency disconnect with immediate socket cleanup
     */
    void emergencyDisconnect();

    /**
     * @brief Test if server is available and responding
     * 
     * @return true if server is reachable and responding, false otherwise
     */
    bool testServerAvailability();

    /**
     * @brief Check server status and availability for TDX client
     * 
     * This method can be called by TDX to proactively check if the server
     * is still available before performing operations
     * 
     * @return json Status information including availability and connection health
     */
    json checkServerStatus();

    /**
     * @brief Send a JSON request and receive response
     * 
     * @param message The JSON message to send
     * @return json The response from server, empty JSON on error
     */
    json sendRequest(const json& message);

    /**
     * @brief Test heartbeat functionality
     * 
     * @return json Server response
     */
    json testHeartbeat();

    /**
     * @brief Send single K-bar data to server
     * 
     * @param kbar_data The K-bar data to send
     * @return json Server response
     */
    json testSingleKBar(const KBarData& kbar_data);

    /**
     * @brief Send K-bar data series to server
     * 
     * @param symbol The symbol for the K-bar series
     * @param kbar_series Vector of K-bar data
     * @param period The period/timeframe for the K-bar series
     * @return json Server response
     */
    json SendKBarSeries(const std::string& symbol, const int period, const std::vector<KBarData>& kbar_series);

    /**
     * @brief Test API calls for indicators
     * 
     * @param requests Vector of API requests
     * @return json Server response
     */
    json testApiCalls(const std::vector<ApiRequest>& requests);

    /**
     * @brief Set a parameter on the server
     * 
     * @param name Parameter name
     * @param value Parameter value
     * @return json Server response
     */
    json setParameter(const std::string& name, const json& value);

    /**
     * @brief Get a parameter from the server
     * 
     * @param name Parameter name
     * @return json Server response
     */
    json getParameter(const std::string& name);

    /**
     * @brief Get server information
     * 
     * @return json Server response
     */
    json getServerInfo();

    /**
     * @brief Get all parameters from server
     * 
     * @return json Server response
     */
    json getAllParameters();


    /**
     * @brief Helper method to create Simple Moving Average request
     * 
     * @param price_data Vector of price data
     * @param period Period for SMA calculation
     * @return json Server response
     */
    json calculateSMA(const std::vector<double>& price_data, int period);

    /**
     * @brief Check if all required dependencies are available
     * 
     * @return true if all dependencies are available, false otherwise
     */
    bool areDependenciesAvailable() const;

    /**
     * @brief Get detailed dependency status information
     * 
     * @return std::string Detailed status of dependencies
     */
    std::string getDependencyStatus() const;

    /**
     * @brief Attempt to reconnect to server with better error recovery
     * 
     * @return true if reconnection successful, false otherwise
     */
    bool reconnect();

    /**
     * @brief Force close ZMQ context to prevent hanging during DLL unload
     * 
     * This method should only be called during DLL unload to ensure
     * ZMQ context is terminated before destructor is called.
     */
    void forceCloseContext();

private:
    /**
     * @brief Get current timestamp in ISO format
     * 
     * @return std::string Current timestamp
     */
    std::string getCurrentTimestamp();

    /**
     * @brief Convert KBarData to JSON
     * 
     * @param kbar The K-bar data to convert
     * @return json JSON representation
     */
    json kbarToJson(const KBarData& kbar);

    /**
     * @brief Convert ApiRequest to JSON
     * 
     * @param request The API request to convert
     * @return json JSON representation
     */
    json apiRequestToJson(const ApiRequest& request);
};

} // namespace QAUtils
