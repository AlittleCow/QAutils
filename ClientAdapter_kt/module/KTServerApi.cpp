#ifdef ENABLE_SERVER_FUNCTIONS

#include "KTServerApi.h"
#include <iostream>
#include <chrono>
#include <iomanip>
#include <sstream>

namespace QAUtils {

/**
 * @brief Construct a new KTZmqClient object
 * 
 * @param server_host The hostname or IP address of the server
 * @param server_port The port number of the server
 */
KTZmqClient::KTZmqClient(const std::string& server_host, int server_port)
    : server_host_(server_host), server_port_(server_port), connected_(false), context_closed_(false) {
    context_ = std::make_unique<zmq::context_t>(1);
    socket_ = std::make_unique<zmq::socket_t>(*context_, zmq::socket_type::req);
}

/**
 * @brief Destroy the KTZmqClient object and cleanup resources
 */
KTZmqClient::~KTZmqClient() {
    log_debug("KTZmqClient destructor called");
    
    if (!context_closed_) {
        try {
            if (connected_) {
                disconnect();
            }
            
            if (socket_) {
                socket_->close();
                socket_.reset();
            }
            
            if (context_) {
                context_->close();
                context_.reset();
            }
        } catch (const std::exception& e) {
            log_error("Exception in KTZmqClient destructor: %s", e.what());
        }
    }
    
    log_debug("KTZmqClient destructor completed");
}

/**
 * @brief Connect to the QuantServer
 * 
 * @return true if connection successful, false otherwise
 */
bool KTZmqClient::connect() {
    if (context_closed_) {
        log_error("Cannot connect: ZMQ context has been force-closed");
        return false;
    }
    
    try {
        std::string endpoint = "tcp://" + server_host_ + ":" + std::to_string(server_port_);
        log_debug("Attempting to connect to %s", endpoint.c_str());
        
        socket_->connect(endpoint);
        
        // Set socket options for better reliability
        int timeout = 5000; // 5 seconds
        socket_->set(zmq::sockopt::rcvtimeo, timeout);
        socket_->set(zmq::sockopt::sndtimeo, timeout);
        socket_->set(zmq::sockopt::linger, 0);
        
        connected_ = true;
        log_debug("Successfully connected to QuantServer at %s", endpoint.c_str());
        return true;
    } catch (const zmq::error_t& e) {
        log_error("ZMQ error during connection: %s", e.what());
        connected_ = false;
        return false;
    } catch (const std::exception& e) {
        log_error("Exception during connection: %s", e.what());
        connected_ = false;
        return false;
    }
}

/**
 * @brief Disconnect from the QuantServer
 */
void KTZmqClient::disconnect() {
    if (!connected_) {
        log_debug("Already disconnected from QuantServer");
        return;
    }
    
    try {
        if (socket_) {
            socket_->disconnect("tcp://" + server_host_ + ":" + std::to_string(server_port_));
        }
        connected_ = false;
        log_debug("Disconnected from QuantServer");
    } catch (const zmq::error_t& e) {
        log_error("ZMQ error during disconnection: %s", e.what());
        connected_ = false;
    } catch (const std::exception& e) {
        log_error("Exception during disconnection: %s", e.what());
        connected_ = false;
    }
}

/**
 * @brief Check if client is connected to server
 * 
 * @return true if connected, false otherwise
 */
bool KTZmqClient::isConnected() const {
    return connected_ && !context_closed_;
}

/**
 * @brief Validate connection health by checking socket state
 * 
 * @return true if connection is healthy, false otherwise
 */
bool KTZmqClient::validateConnectionHealth() {
    if (!isConnected()) {
        return false;
    }
    
    try {
        // Send a simple heartbeat to test connection
        json heartbeat_response = testHeartbeat();
        return !heartbeat_response.empty() && heartbeat_response.contains("status");
    } catch (const std::exception& e) {
        log_error("Connection health check failed: %s", e.what());
        return false;
    }
}

/**
 * @brief Emergency disconnect with immediate socket cleanup
 */
void KTZmqClient::emergencyDisconnect() {
    log_debug("Emergency disconnect initiated");
    
    try {
        connected_ = false;
        
        if (socket_) {
            socket_->close();
        }
        
        log_debug("Emergency disconnect completed");
    } catch (const std::exception& e) {
        log_error("Exception during emergency disconnect: %s", e.what());
    }
}

/**
 * @brief Test if server is available and responding
 * 
 * @return true if server is reachable and responding, false otherwise
 */
bool KTZmqClient::testServerAvailability() {
    if (!isConnected()) {
        log_debug("Not connected, attempting to connect for availability test");
        if (!connect()) {
            return false;
        }
    }
    
    try {
        json heartbeat_response = testHeartbeat();
        bool available = !heartbeat_response.empty() && 
                        heartbeat_response.contains("status") && 
                        heartbeat_response["status"] == "ok";
        
        log_debug("Server availability test result: %s", available ? "available" : "unavailable");
        return available;
    } catch (const std::exception& e) {
        log_error("Server availability test failed: %s", e.what());
        return false;
    }
}

/**
 * @brief Check server status and availability for KT client
 * 
 * @return json Status information including availability and connection health
 */
json KTZmqClient::checkServerStatus() {
    json status;
    status["client_connected"] = isConnected();
    status["server_available"] = false;
    status["connection_healthy"] = false;
    status["timestamp"] = this->getCurrentTimestamp();
    
    if (isConnected()) {
        try {
            json server_info = getServerInfo();
            if (!server_info.empty()) {
                status["server_available"] = true;
                status["connection_healthy"] = true;
                status["server_info"] = server_info;
            }
        } catch (const std::exception& e) {
            log_error("Failed to get server status: %s", e.what());
            status["error"] = e.what();
        }
    }
    
    return status;
}

/**
 * @brief Send a JSON request and receive response
 * 
 * @param message The JSON message to send
 * @return json The response from server, empty JSON on error
 */
json KTZmqClient::sendRequest(const json& message) {
    if (!isConnected()) {
        log_error("Cannot send request: not connected to server");
        return json();
    }
    
    try {
        std::string message_str = message.dump();
        log_debug("Sending request: %s", message_str.c_str());
        
        zmq::message_t request(message_str.size());
        memcpy(request.data(), message_str.c_str(), message_str.size());
        
        auto send_result = socket_->send(request, zmq::send_flags::none);
        if (!send_result) {
            log_error("Failed to send request");
            return json();
        }
        
        zmq::message_t reply;
        auto recv_result = socket_->recv(reply, zmq::recv_flags::none);
        if (!recv_result) {
            log_error("Failed to receive response");
            return json();
        }
        
        std::string reply_str(static_cast<char*>(reply.data()), reply.size());
        log_debug("Received response: %s", reply_str.c_str());
        
        return json::parse(reply_str);
    } catch (const zmq::error_t& e) {
        log_error("ZMQ error during request: %s", e.what());
        return json();
    } catch (const json::exception& e) {
        log_error("JSON error during request: %s", e.what());
        return json();
    } catch (const std::exception& e) {
        log_error("Exception during request: %s", e.what());
        return json();
    }
}

/**
 * @brief Test heartbeat functionality
 * 
 * @return json Server response
 */
json KTZmqClient::testHeartbeat() {
    json request;
    request["type"] = "heartbeat";
    request["timestamp"] = this->getCurrentTimestamp();
    request["client_id"] = "kt_client";
    
    return sendRequest(request);
}

/**
 * @brief Send single K-bar data to server
 * 
 * @param kbar_data The K-bar data to send
 * @return json Server response
 */
json KTZmqClient::testSingleKBar(const KTBarData& kbar_data) {
    return testSingleKBar(kbar_data, "1min");
}

/**
 * @brief Send single K-bar data to server with period information
 * 
 * @param kbar_data The K-bar data to send
 * @param period The period/timeframe for the K-bar data
 * @return json Server response
 */
json KTZmqClient::testSingleKBar(const KTBarData& kbar_data, const std::string& period) {
    json request;
    request["type"] = "kbar_data";
    request["data"] = this->kbarToJson(kbar_data);
    request["period"] = period;
    request["timestamp"] = this->getCurrentTimestamp();
    
    return sendRequest(request);
}

/**
 * @brief Send K-bar data series to server
 * 
 * @param symbol The symbol for the K-bar series
 * @param period The period/timeframe for the K-bar series
 * @param kbar_series Vector of K-bar data
 * @return json Server response
 */
json KTZmqClient::SendKBarSeries(const std::string& symbol, const int period, const std::vector<KTBarData>& kbar_series) {
    json request;
    request["type"] = "kbar_series";
    request["symbol"] = symbol;
    request["period"] = period;
    request["timestamp"] = this->getCurrentTimestamp();
    
    json kbar_array = json::array();
    for (const auto& kbar : kbar_series) {
        kbar_array.push_back(this->kbarToJson(kbar));
    }
    request["data"] = kbar_array;
    
    return sendRequest(request);
}

/**
 * @brief Test API calls for indicators
 * 
 * @param requests Vector of API requests
 * @return json Server response
 */
json KTZmqClient::testApiCalls(const std::vector<KTApiRequest>& requests) {
    json request;
    request["type"] = "api_calls";
    request["timestamp"] = this->getCurrentTimestamp();
    
    json api_array = json::array();
    for (const auto& api_req : requests) {
        api_array.push_back(this->apiRequestToJson(api_req));
    }
    request["api_calls"] = api_array;
    
    return sendRequest(request);
}

/**
 * @brief Set a parameter on the server
 * 
 * @param name Parameter name
 * @param value Parameter value
 * @return json Server response
 */
json KTZmqClient::setParameter(const std::string& name, const json& value) {
    json request;
    request["type"] = "set_parameter";
    request["parameter_name"] = name;
    request["parameter_value"] = value;
    request["timestamp"] = this->getCurrentTimestamp();
    
    return sendRequest(request);
}

/**
 * @brief Get a parameter from the server
 * 
 * @param name Parameter name
 * @return json Server response
 */
json KTZmqClient::getParameter(const std::string& name) {
    json request;
    request["type"] = "get_parameter";
    request["parameter_name"] = name;
    request["timestamp"] = this->getCurrentTimestamp();
    
    return sendRequest(request);
}

/**
 * @brief Get server information
 * 
 * @return json Server response
 */
json KTZmqClient::getServerInfo() {
    json request;
    request["type"] = "server_info";
    request["timestamp"] = this->getCurrentTimestamp();
    
    return sendRequest(request);
}

/**
 * @brief Get all parameters from server
 * 
 * @return json Server response
 */
json KTZmqClient::getAllParameters() {
    json request;
    request["type"] = "get_all_parameters";
    request["timestamp"] = this->getCurrentTimestamp();
    
    return sendRequest(request);
}

/**
 * @brief Helper method to create Simple Moving Average request
 * 
 * @param price_data Vector of price data
 * @param period Period for SMA calculation
 * @return json Server response
 */
json KTZmqClient::calculateSMA(const std::vector<double>& price_data, int period) {
    KTApiRequest sma_request;
    sma_request.indicator_name = "SMA";
    sma_request.indicator_function_name = "calculate_sma";
    sma_request.parameters["price_data"] = price_data;
    sma_request.parameters["period"] = period;
    sma_request.result_required = true;
    
    return testApiCalls({sma_request});
}

/**
 * @brief Check if all required dependencies are available
 * 
 * @return true if all dependencies are available, false otherwise
 */
bool KTZmqClient::areDependenciesAvailable() const {
    // Check if ZMQ context and socket are available
    return context_ != nullptr && socket_ != nullptr && !context_closed_;
}

/**
 * @brief Get detailed dependency status information
 * 
 * @return std::string Detailed status of dependencies
 */
std::string KTZmqClient::getDependencyStatus() const {
    std::ostringstream status;
    status << "KTZmqClient Dependency Status:\n";
    status << "  ZMQ Context: " << (context_ ? "Available" : "Not Available") << "\n";
    status << "  ZMQ Socket: " << (socket_ ? "Available" : "Not Available") << "\n";
    status << "  Context Closed: " << (context_closed_ ? "Yes" : "No") << "\n";
    status << "  Connected: " << (connected_ ? "Yes" : "No") << "\n";
    return status.str();
}

/**
 * @brief Attempt to reconnect to server with better error recovery
 * 
 * @return true if reconnection successful, false otherwise
 */
bool KTZmqClient::reconnect() {
    log_debug("Attempting to reconnect to QuantServer");
    
    if (connected_) {
        disconnect();
    }
    
    // Recreate socket if needed
    if (!socket_ || context_closed_) {
        try {
            if (context_closed_ || !context_) {
                context_ = std::make_unique<zmq::context_t>(1);
                context_closed_ = false;
            }
            socket_ = std::make_unique<zmq::socket_t>(*context_, zmq::socket_type::req);
        } catch (const std::exception& e) {
            log_error("Failed to recreate socket during reconnect: %s", e.what());
            return false;
        }
    }
    
    return connect();
}

/**
 * @brief Force close ZMQ context to prevent hanging during DLL unload
 */
void KTZmqClient::forceCloseContext() {
    log_debug("Force closing ZMQ context");
    
    try {
        connected_ = false;
        context_closed_ = true;
        
        if (socket_) {
            socket_->close();
            socket_.reset();
        }
        
        if (context_) {
            context_->close();
            context_.reset();
        }
        
        log_debug("ZMQ context force-closed successfully");
    } catch (const std::exception& e) {
        log_error("Exception during force close: %s", e.what());
    }
}

/**
 * @brief Get current timestamp in ISO format
 * 
 * @return std::string Current timestamp
 */
std::string KTZmqClient::getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    
    std::ostringstream oss;
    oss << std::put_time(std::gmtime(&time_t), "%Y-%m-%dT%H:%M:%S");
    oss << '.' << std::setfill('0') << std::setw(3) << ms.count() << 'Z';
    return oss.str();
}

/**
 * @brief Convert KTBarData to JSON
 * 
 * @param kbar The K-bar data to convert
 * @return json JSON representation
 */
json KTZmqClient::kbarToJson(const KTBarData& kbar) {
    json j;
    j["symbol"] = kbar.symbol;
    j["timestamp"] = kbar.timestamp;
    j["open"] = kbar.open;
    j["high"] = kbar.high;
    j["low"] = kbar.low;
    j["close"] = kbar.close;
    j["volume"] = kbar.volume;
    return j;
}

/**
 * @brief Convert KTApiRequest to JSON
 * 
 * @param request The API request to convert
 * @return json JSON representation
 */
json KTZmqClient::apiRequestToJson(const KTApiRequest& request) {
    json j;
    j["indicator_name"] = request.indicator_name;
    j["indicator_function_name"] = request.indicator_function_name;
    j["parameters"] = request.parameters;
    j["result_required"] = request.result_required;
    return j;
}

} // namespace QAUtils

#endif // ENABLE_SERVER_FUNCTIONS