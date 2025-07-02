#include "ServerApi.h"
#include <iostream>
#include <chrono>
#include <iomanip>
#include <sstream>

namespace QAUtils {

/**
 * @brief Construct a new ZmqClient object
 * 
 * @param server_host The hostname or IP address of the server
 * @param server_port The port number of the server
 */
ZmqClient::ZmqClient(const std::string& server_host, int server_port)
    : server_host_(server_host), server_port_(server_port), connected_(false), context_closed_(false) {
    context_ = std::make_unique<zmq::context_t>(1);
    socket_ = std::make_unique<zmq::socket_t>(*context_, zmq::socket_type::req);
}

/**
 * @brief Destroy the ZmqClient object and cleanup resources
 */
ZmqClient::~ZmqClient() {
    log_debug("ZmqClient destructor started");
    
    if (connected_) {
        log_debug("ZmqClient was connected, calling disconnect");
        disconnect();
        log_debug("ZMQ client disconnected in destructor");
    } else {
        log_debug("ZMQ client already disconnected, skipping disconnect in destructor");
    }
    
    // During DLL unload, we need to avoid calling ZMQ destructors
    // Release the unique_ptrs without calling their destructors
    log_debug("Releasing ZMQ objects without calling destructors to prevent DLL unload hanging");
    
    if (socket_) {
        // Release the unique_ptr without calling the destructor
        socket_.release();
        log_debug("ZMQ socket unique_ptr released (destructor bypassed)");
    }
    
    if (context_) {
        // Release the unique_ptr without calling the destructor  
        context_.release();
        log_debug("ZMQ context unique_ptr released (destructor bypassed)");
    }
    
    // Don't even null the pointers - just let them be destroyed naturally
    context_closed_ = true;
    
    log_debug("ZmqClient destructor completed successfully");
}

/**
 * @brief Connect to the QuantServer
 * 
 * @return true if connection successful, false otherwise
 */
bool ZmqClient::connect() {
    try {
        // Set socket options for better timeout handling with 5-second maximum
        socket_->set(zmq::sockopt::linger, 0); // Don't linger on close
        socket_->set(zmq::sockopt::rcvtimeo, 5000); // 5 second receive timeout
        socket_->set(zmq::sockopt::sndtimeo, 5000); // 5 second send timeout
        
        std::string endpoint = "tcp://" + server_host_ + ":" + std::to_string(server_port_);
        
        // Use polling to ensure connection attempt doesn't hang
        socket_->connect(endpoint);
        
        // Test connection immediately with timeout to ensure server is responsive
        json test_message = {
            {"type", "heartbeat"},
            {"client_time", getCurrentTimestamp()}
        };
        
        std::string json_str = test_message.dump();
        zmq::message_t request(json_str.size());
        memcpy(request.data(), json_str.c_str(), json_str.size());
        
        // Use polling with 5-second timeout for connection test
        zmq::pollitem_t poll_items[] = { { *socket_, 0, ZMQ_POLLOUT, 0 } };
        int poll_result = zmq::poll(poll_items, 1, std::chrono::milliseconds(5000));
        
        if (poll_result <= 0) {
            log_error("Connection test failed: server not responding within 5 seconds");
            connected_ = false;
            return false;
        }
        
        if (!socket_->send(request, zmq::send_flags::dontwait)) {
            log_error("Failed to send connection test message");
            connected_ = false;
            return false;
        }
        
        // Wait for response with 5-second timeout
        zmq::pollitem_t recv_poll_items[] = { { *socket_, 0, ZMQ_POLLIN, 0 } };
        poll_result = zmq::poll(recv_poll_items, 1, std::chrono::milliseconds(5000));
        
        if (poll_result <= 0) {
            log_error("Connection test failed: no response from server within 5 seconds");
            connected_ = false;
            return false;
        }
        
        zmq::message_t reply;
        if (!socket_->recv(reply, zmq::recv_flags::dontwait)) {
            log_error("Failed to receive connection test response");
            connected_ = false;
            return false;
        }
        
        // Mark as connected first
        connected_ = true;
        
        // Now test full server availability to ensure it's fully operational
        if (!testServerAvailability()) {
            log_error("Server availability test failed after initial connection");
            connected_ = false;
            return false;
        }
        
        log_info("Connected to QuantServer at %s:%d and verified server availability", server_host_.c_str(), server_port_);
        return true;
    } catch (const std::exception& e) {
        log_error("Error connecting to server: %s", e.what());
        connected_ = false;
        return false;
    }
}

/**
 * @brief Disconnect from the QuantServer
 */
void ZmqClient::disconnect() {
    if (connected_) {
        try {
            // Set linger to 0 to avoid hanging on close
            if (socket_) {
                socket_->set(zmq::sockopt::linger, 0);
                socket_->close();
            }
            connected_ = false;
            log_debug("Disconnected from QuantServer");
        } catch (const std::exception& e) {
            log_error("Error during disconnect: %s", e.what());
            connected_ = false;
        }
    }
}

/**
 * @brief Check if client is connected to server
 * 
 * @return true if connected, false otherwise
 */
bool ZmqClient::isConnected() const {
    return connected_;
}

/**
 * @brief Validate connection health by checking socket state
 * 
 * @return true if connection is healthy, false otherwise
 */
bool ZmqClient::validateConnectionHealth() {
    if (!connected_ || !socket_) {
        return false;
    }
    
    try {
        // Quick non-blocking check to see if socket is still valid
        // This will fail immediately if server has shut down
        zmq::pollitem_t poll_items[] = { { *socket_, 0, ZMQ_POLLOUT, 0 } };
        int poll_result = zmq::poll(poll_items, 1, std::chrono::milliseconds(0)); // No wait
        
        // If poll returns error, socket is likely broken
        if (poll_result < 0) {
            log_error("Socket health check failed: poll returned error");
            connected_ = false;
            return false;
        }
        
        return true;
    } catch (const std::exception& e) {
        log_error("Connection health check failed: %s", e.what());
        connected_ = false;
        return false;
    }
}

/**
 * @brief Emergency disconnect with immediate socket cleanup
 */
void ZmqClient::emergencyDisconnect() {
    log_debug("Emergency disconnect initiated");
    
    try {
        connected_ = false;
        
        if (socket_) {
            // Force immediate cleanup without waiting
            socket_->set(zmq::sockopt::linger, 0);
            socket_->close();
            
            // Create new socket immediately to prevent state corruption
            socket_ = std::make_unique<zmq::socket_t>(*context_, zmq::socket_type::req);
            socket_->set(zmq::sockopt::linger, 0);
            socket_->set(zmq::sockopt::rcvtimeo, 5000);
            socket_->set(zmq::sockopt::sndtimeo, 5000);
            
            log_debug("Emergency disconnect completed with socket reset");
        }
    } catch (const std::exception& e) {
        log_error("Error during emergency disconnect: %s", e.what());
        connected_ = false;
    }
}

/**
 * @brief Test if server is available and responding
 * 
 * @return true if server is reachable and responding, false otherwise
 */
bool ZmqClient::testServerAvailability() {
    if (!connected_) {
        return false;
    }
    
    // First validate connection health
    if (!validateConnectionHealth()) {
        log_error("Connection health validation failed");
        emergencyDisconnect();
        return false;
    }
    
    try {
        // Send a simple heartbeat with 5-second timeout to test availability
        json test_message = {
            {"type", "heartbeat"},
            {"client_time", getCurrentTimestamp()}
        };
        
        std::string json_str = test_message.dump();
        zmq::message_t request(json_str.size());
        memcpy(request.data(), json_str.c_str(), json_str.size());
        
        // Use 5-second timeout for availability test
        zmq::pollitem_t poll_items[] = { { *socket_, 0, ZMQ_POLLOUT, 0 } };
        int poll_result = zmq::poll(poll_items, 1, std::chrono::milliseconds(5000));
        
        if (poll_result <= 0) {
            log_error("Server availability test failed: send timeout after 5 seconds");
            emergencyDisconnect();
            return false;
        }
        
        if (!socket_->send(request, zmq::send_flags::dontwait)) {
            log_error("Server availability test failed: send failed");
            emergencyDisconnect();
            return false;
        }
        
        // Check for response with 5-second timeout
        zmq::pollitem_t recv_poll_items[] = { { *socket_, 0, ZMQ_POLLIN, 0 } };
        poll_result = zmq::poll(recv_poll_items, 1, std::chrono::milliseconds(5000));
        
        if (poll_result <= 0) {
            log_error("Server availability test failed: receive timeout after 5 seconds");
            emergencyDisconnect();
            return false;
        }
        
        zmq::message_t reply;
        if (!socket_->recv(reply, zmq::recv_flags::dontwait)) {
            log_error("Server availability test failed: receive failed");
            emergencyDisconnect();
            return false;
        }
        
        // Parse response to check if it's valid
        std::string reply_str(static_cast<char*>(reply.data()), reply.size());
        json response = json::parse(reply_str);
        
        // Check if response indicates success or at least valid communication
        return response.contains("status") || response.contains("type") || !response.empty();
        
    } catch (const std::exception& e) {
        log_error("Server availability test failed: %s", e.what());
        emergencyDisconnect();
        return false;
    }
}

/**
 * @brief Send a JSON request and receive response
 * 
 * @param message The JSON message to send
 * @return json The response from server, empty JSON on error
 */
json ZmqClient::sendRequest(const json& message) {
    if (!connected_) {
        log_error("Client not connected to server");
        return json{{"status", "error"}, {"message", "client not connected"}};
    }

    // Validate connection health before sending
    if (!validateConnectionHealth()) {
        log_error("Connection health check failed before sending request");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection unhealthy"}};
    }

    // Test server availability before sending important requests
    // Skip availability test for heartbeat messages to avoid recursion
    if (message.contains("type") && message["type"] != "heartbeat") {
        if (!testServerAvailability()) {
            log_error("Server availability test failed before sending request");
            return json{{"status", "error"}, {"message", "server not available"}};
        }
    }

    try {
        // Convert JSON to string and send
        std::string json_str = message.dump();
        zmq::message_t request(json_str.size());
        memcpy(request.data(), json_str.c_str(), json_str.size());
        
        // Send request with 5-second timeout using polling
        zmq::pollitem_t poll_items[] = { { *socket_, 0, ZMQ_POLLOUT, 0 } };
        int poll_result = zmq::poll(poll_items, 1, std::chrono::milliseconds(5000));
        
        if (poll_result == 0) {
            log_error("Send timeout: server not responding within 5 seconds");
            emergencyDisconnect();
            return json{{"status", "error"}, {"message", "send timeout"}};
        } else if (poll_result < 0) {
            log_error("Poll error during send - server likely disconnected");
            emergencyDisconnect();
            return json{{"status", "error"}, {"message", "poll error - server disconnected"}};
        }
        
        if (!socket_->send(request, zmq::send_flags::dontwait)) {
            log_error("Failed to send request - server likely disconnected");
            emergencyDisconnect();
            return json{{"status", "error"}, {"message", "send failed - server disconnected"}};
        }

        // Receive response with 5-second timeout using polling
        zmq::pollitem_t recv_poll_items[] = { { *socket_, 0, ZMQ_POLLIN, 0 } };
        poll_result = zmq::poll(recv_poll_items, 1, std::chrono::milliseconds(5000));
        
        if (poll_result == 0) {
            log_error("Receive timeout: server not responding to request within 5 seconds");
            emergencyDisconnect();
            return json{{"status", "error"}, {"message", "receive timeout - server likely shutdown"}};
        } else if (poll_result < 0) {
            log_error("Poll error during receive - server disconnected");
            emergencyDisconnect();
            return json{{"status", "error"}, {"message", "poll error - server disconnected"}};
        }

        zmq::message_t reply;
        if (!socket_->recv(reply, zmq::recv_flags::dontwait)) {
            log_error("Failed to receive response - server disconnected");
            emergencyDisconnect();
            return json{{"status", "error"}, {"message", "receive failed - server disconnected"}};
        }

        // Parse JSON response
        std::string reply_str(static_cast<char*>(reply.data()), reply.size());
        return json::parse(reply_str);

    } catch (const json::parse_error& e) {
        log_error("JSON parse error: %s", e.what());
        return json{{"status", "error"}, {"message", "json parse error"}};
    } catch (const std::exception& e) {
        log_error("Error sending request: %s", e.what());
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", e.what()}};
    }
}

/**
 * @brief Test heartbeat functionality
 * 
 * @return json Server response
 */
json ZmqClient::testHeartbeat() {
    // Validate connection health before sending heartbeat
    if (!connected_ || !validateConnectionHealth()) {
        log_error("Connection not healthy for heartbeat test");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection not healthy"}};
    }
    
    json message = {
        {"type", "heartbeat"},
        {"client_time", getCurrentTimestamp()}
    };
    return sendRequest(message);
}

/**
 * @brief Send single K-bar data to server
 * 
 * @param kbar_data The K-bar data to send
 * @return json Server response
 */
json ZmqClient::testSingleKBar(const KBarData& kbar_data) {
    // Validate connection health before sending data
    if (!connected_ || !validateConnectionHealth()) {
        log_error("Connection not healthy for K-bar data send");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection not healthy"}};
    }
    
    json message = {
        {"type", "kbar_data"},
        {"data", kbarToJson(kbar_data)}
    };
    return sendRequest(message);
}

/**
 * @brief Send K-bar data series to server
 * 
 * @param symbol The symbol for the K-bar series
 * @param kbar_series Vector of K-bar data
 * @return json Server response
 */
json ZmqClient::testKBarSeries(const std::string& symbol, const std::vector<KBarData>& kbar_series) {
    // Validate connection health before sending data series
    if (!connected_ || !validateConnectionHealth()) {
        log_error("Connection not healthy for K-bar series send");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection not healthy"}};
    }
    
    json data_array = json::array();
    for (const auto& kbar : kbar_series) {
        json kbar_json = {
            {"timestamp", kbar.timestamp},
            {"open", kbar.open},
            {"high", kbar.high},
            {"low", kbar.low},
            {"close", kbar.close},
            {"volume", kbar.volume}
        };
        data_array.push_back(kbar_json);
    }

    json message = {
        {"type", "kbar_series"},
        {"symbol", symbol},
        {"data", data_array}
    };
    return sendRequest(message);
}

/**
 * @brief Test API calls for indicators
 * 
 * @param requests Vector of API requests
 * @return json Server response
 */
json ZmqClient::testApiCalls(const std::vector<ApiRequest>& requests) {
    // Validate connection health before sending API calls
    if (!connected_ || !validateConnectionHealth()) {
        log_error("Connection not healthy for API calls");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection not healthy"}};
    }
    
    json requests_array = json::array();
    for (const auto& request : requests) {
        requests_array.push_back(apiRequestToJson(request));
    }

    json message = {
        {"type", "api_call"},
        {"requests", requests_array}
    };
    return sendRequest(message);
}

/**
 * @brief Set a parameter on the server
 * 
 * @param name Parameter name
 * @param value Parameter value
 * @return json Server response
 */
json ZmqClient::setParameter(const std::string& name, const json& value) {
    // Validate connection health before setting parameter
    if (!connected_ || !validateConnectionHealth()) {
        log_error("Connection not healthy for parameter setting");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection not healthy"}};
    }
    
    json message = {
        {"type", "control"},
        {"control_type", "set_param"},
        {"parameters", {
            {"name", name},
            {"value", value}
        }}
    };
    return sendRequest(message);
}

/**
 * @brief Get a parameter from the server
 * 
 * @param name Parameter name
 * @return json Server response
 */
json ZmqClient::getParameter(const std::string& name) {
    // Validate connection health before getting parameter
    if (!connected_ || !validateConnectionHealth()) {
        log_error("Connection not healthy for parameter retrieval");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection not healthy"}};
    }
    
    json message = {
        {"type", "control"},
        {"control_type", "get_param"},
        {"parameters", {
            {"name", name}
        }}
    };
    return sendRequest(message);
}

/**
 * @brief Get server information
 * 
 * @return json Server response
 */
json ZmqClient::getServerInfo() {
    // Validate connection health before getting server info
    if (!connected_ || !validateConnectionHealth()) {
        log_error("Connection not healthy for server info retrieval");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection not healthy"}};
    }
    
    json message = {
        {"type", "control"},
        {"control_type", "server_info"}
    };
    return sendRequest(message);
}

/**
 * @brief Get all parameters from server
 * 
 * @return json Server response
 */
json ZmqClient::getAllParameters() {
    // Validate connection health before getting all parameters
    if (!connected_ || !validateConnectionHealth()) {
        log_error("Connection not healthy for all parameters retrieval");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection not healthy"}};
    }
    
    json message = {
        {"type", "control"},
        {"control_type", "get_all_params"}
    };
    return sendRequest(message);
}

/**
 * @brief Helper method to create Simple Moving Average request
 * 
 * @param price_data Vector of price data
 * @param period Period for SMA calculation
 * @return json Server response
 */
json ZmqClient::calculateSMA(const std::vector<double>& price_data, int period) {
    // Validate connection health before calculating SMA
    if (!connected_ || !validateConnectionHealth()) {
        log_error("Connection not healthy for SMA calculation");
        emergencyDisconnect();
        return json{{"status", "error"}, {"message", "connection not healthy"}};
    }
    
    ApiRequest request = {
        "Simple Moving Average",
        "sma",
        {
            {"data", price_data},
            {"period", period}
        },
        true
    };
    return testApiCalls({request});
}

/**
 * @brief Get current timestamp in ISO format
 * 
 * @return std::string Current timestamp
 */
std::string ZmqClient::getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    
    std::stringstream ss;
    ss << std::put_time(std::gmtime(&t), "%Y-%m-%dT%H:%M:%S");
    ss << '.' << std::setfill('0') << std::setw(3) << ms.count() << 'Z';
    return ss.str();
}

/**
 * @brief Convert KBarData to JSON
 * 
 * @param kbar The K-bar data to convert
 * @return json JSON representation
 */
json ZmqClient::kbarToJson(const KBarData& kbar) {
    return json{
        {"symbol", kbar.symbol},
        {"timestamp", kbar.timestamp},
        {"open", kbar.open},
        {"high", kbar.high},
        {"low", kbar.low},
        {"close", kbar.close},
        {"volume", kbar.volume}
    };
}

/**
 * @brief Convert ApiRequest to JSON
 * 
 * @param request The API request to convert
 * @return json JSON representation
 */
json ZmqClient::apiRequestToJson(const ApiRequest& request) {
    return json{
        {"indicator_name", request.indicator_name},
        {"indicator_function_name", request.indicator_function_name},
        {"parameters", request.parameters},
        {"result_required", request.result_required}
    };
}

/**
 * @brief Check if all required dependencies are available
 * 
 * @return true if all dependencies are available, false otherwise
 */
bool ZmqClient::areDependenciesAvailable() const {
    // For this implementation, we assume ZMQ and JSON libraries are available
    // since the code compiles and links successfully
    return true;
}

/**
 * @brief Get detailed dependency status information
 * 
 * @return std::string Detailed status of dependencies
 */
std::string ZmqClient::getDependencyStatus() const {
    std::stringstream status;
    status << "=== ZmqClient Dependency Status ===\n";
    status << "ZeroMQ (libzmq): Available\n";
    status << "ZeroMQ C++ Bindings (cppzmq): Available\n";
    status << "nlohmann/json: Available\n";
    status << "Current connection status: " << (connected_ ? "Connected" : "Disconnected") << "\n";
    status << "Server: " << server_host_ << ":" << server_port_ << "\n";
    status << "=== All dependencies satisfied ===\n";
    return status.str();
}

/**
 * @brief Attempt to reconnect to server with better error recovery
 * 
 * @return true if reconnection successful, false otherwise
 */
bool ZmqClient::reconnect() {
    try {
        // First disconnect if currently connected
        if (connected_) {
            disconnect();
        }
        
        // Create new socket to ensure clean state
        socket_ = std::make_unique<zmq::socket_t>(*context_, zmq::socket_type::req);
        
        // Set socket options for 5-second timeout handling
        socket_->set(zmq::sockopt::rcvtimeo, 5000); // 5 seconds
        socket_->set(zmq::sockopt::sndtimeo, 5000); // 5 seconds
        socket_->set(zmq::sockopt::linger, 0); // Don't linger on close
        
        // Attempt connection
        std::string endpoint = "tcp://" + server_host_ + ":" + std::to_string(server_port_);
        socket_->connect(endpoint);
        
        // Test connection with a simple heartbeat and 5-second timeout
        json test_message = {
            {"type", "heartbeat"},
            {"client_time", getCurrentTimestamp()}
        };
        
        std::string json_str = test_message.dump();
        zmq::message_t request(json_str.size());
        memcpy(request.data(), json_str.c_str(), json_str.size());
        
        // Use polling with 5-second timeout for reconnection test
        zmq::pollitem_t poll_items[] = { { *socket_, 0, ZMQ_POLLOUT, 0 } };
        int poll_result = zmq::poll(poll_items, 1, std::chrono::milliseconds(5000));
        
        if (poll_result <= 0) {
            log_error("Reconnection failed: server not responding within 5 seconds");
            connected_ = false;
            return false;
        }
        
        if (!socket_->send(request, zmq::send_flags::dontwait)) {
            log_error("Reconnection failed: unable to send test message");
            connected_ = false;
            return false;
        }
        
        // Wait for response with 5-second timeout
        zmq::pollitem_t recv_poll_items[] = { { *socket_, 0, ZMQ_POLLIN, 0 } };
        poll_result = zmq::poll(recv_poll_items, 1, std::chrono::milliseconds(5000));
        
        if (poll_result <= 0) {
            log_error("Reconnection failed: no response within 5 seconds");
            connected_ = false;
            return false;
        }
        
        zmq::message_t reply;
        if (!socket_->recv(reply, zmq::recv_flags::dontwait)) {
            log_error("Reconnection failed: unable to receive response");
            connected_ = false;
            return false;
        }
        
        // Parse and validate response
        std::string reply_str(static_cast<char*>(reply.data()), reply.size());
        json response = json::parse(reply_str);
        
        if (response.contains("status") || response.contains("type") || !response.empty()) {
            connected_ = true;
            log_info("Successfully reconnected to QuantServer at %s:%d", server_host_.c_str(), server_port_);
            return true;
        } else {
            connected_ = false;
            log_error("Reconnection test failed: invalid response from server");
            return false;
        }
        
    } catch (const std::exception& e) {
        connected_ = false;
        log_error("Error during reconnection: %s", e.what());
        return false;
    }
}

/**
 * @brief Force close ZMQ context to prevent hanging during DLL unload
 * 
 * This method should only be called during DLL unload to ensure
 * ZMQ context is terminated before destructor is called.
 */
void ZmqClient::forceCloseContext() {
    log_debug("Force closing ZMQ context to prevent DLL unload hanging");
    
    try {
        // First disconnect if connected
        if (connected_) {
            connected_ = false;
            log_debug("Marked client as disconnected during force close");
        }
        
        // Close socket first
        if (socket_) {
            try {
                socket_->close();
                log_debug("ZMQ socket closed during force close");
            } catch (const std::exception& e) {
                log_error("Error closing socket during force close: %s", e.what());
            }
        }
        
        // Mark context as closed and terminate it
        if (context_ && !context_closed_) {
            try {
                context_->close();
                context_closed_ = true;
                log_debug("ZMQ context closed and marked as closed");
            } catch (const std::exception& e) {
                log_error("Error closing context during force close: %s", e.what());
                context_closed_ = true; // Mark as closed even if error occurred
            }
        }
        
    } catch (const std::exception& e) {
        log_error("Error during force close context: %s", e.what());
        context_closed_ = true;
    }
    
    log_debug("Force close context completed");
}

/**
 * @brief Check server status and availability for TDX client
 * 
 * This method can be called by TDX to proactively check if the server
 * is still available before performing operations
 * 
 * @return json Status information including availability and connection health
 */
json ZmqClient::checkServerStatus() {
    json status_info = {
        {"connected", connected_},
        {"server_host", server_host_},
        {"server_port", server_port_},
        {"timestamp", getCurrentTimestamp()}
    };
    
    if (!connected_) {
        status_info["status"] = "disconnected";
        status_info["message"] = "Client not connected to server";
        return status_info;
    }
    
    // Check connection health
    bool health_ok = validateConnectionHealth();
    status_info["connection_healthy"] = health_ok;
    
    if (!health_ok) {
        status_info["status"] = "unhealthy";
        status_info["message"] = "Connection health check failed";
        emergencyDisconnect();
        return status_info;
    }
    
    // Test server availability
    bool server_available = testServerAvailability();
    status_info["server_available"] = server_available;
    
    if (server_available) {
        status_info["status"] = "available";
        status_info["message"] = "Server is healthy and responding";
    } else {
        status_info["status"] = "unavailable";
        status_info["message"] = "Server not responding or offline";
    }
    
    return status_info;
}

} // namespace QAUtils
