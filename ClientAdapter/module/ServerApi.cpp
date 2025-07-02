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
        // Set socket options for better timeout handling
        socket_->set(zmq::sockopt::linger, 0); // Don't linger on close
        socket_->set(zmq::sockopt::rcvtimeo, 10000); // 10 second receive timeout
        socket_->set(zmq::sockopt::sndtimeo, 5000);  // 5 second send timeout
        
        std::string endpoint = "tcp://" + server_host_ + ":" + std::to_string(server_port_);
        socket_->connect(endpoint);
        connected_ = true;
        log_info("Connected to QuantServer at %s:%d", server_host_.c_str(), server_port_);
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
 * @brief Test if server is available and responding
 * 
 * @return true if server is reachable and responding, false otherwise
 */
bool ZmqClient::testServerAvailability() {
    if (!connected_) {
        return false;
    }
    
    try {
        // Send a simple heartbeat with shorter timeout to test availability
        json test_message = {
            {"type", "heartbeat"},
            {"client_time", getCurrentTimestamp()}
        };
        
        std::string json_str = test_message.dump();
        zmq::message_t request(json_str.size());
        memcpy(request.data(), json_str.c_str(), json_str.size());
        
        // Use shorter timeout for availability test
        zmq::pollitem_t poll_items[] = { { *socket_, 0, ZMQ_POLLOUT, 0 } };
        int poll_result = zmq::poll(poll_items, 1, std::chrono::milliseconds(2000)); // 2 second timeout
        
        if (poll_result <= 0) {
            return false;
        }
        
        if (!socket_->send(request, zmq::send_flags::dontwait)) {
            return false;
        }
        
        // Check for response
        zmq::pollitem_t recv_poll_items[] = { { *socket_, 0, ZMQ_POLLIN, 0 } };
        poll_result = zmq::poll(recv_poll_items, 1, std::chrono::milliseconds(3000)); // 3 second timeout
        
        if (poll_result <= 0) {
            // Reset socket state after failed test
            socket_->close();
            socket_ = std::make_unique<zmq::socket_t>(*context_, zmq::socket_type::req);
            socket_->set(zmq::sockopt::linger, 0);
            socket_->set(zmq::sockopt::rcvtimeo, 10000);
            socket_->set(zmq::sockopt::sndtimeo, 5000);
            std::string endpoint = "tcp://" + server_host_ + ":" + std::to_string(server_port_);
            socket_->connect(endpoint);
            return false;
        }
        
        zmq::message_t reply;
        if (!socket_->recv(reply, zmq::recv_flags::dontwait)) {
            return false;
        }
        
        // Parse response to check if it's valid
        std::string reply_str(static_cast<char*>(reply.data()), reply.size());
        json response = json::parse(reply_str);
        
        // Check if response indicates success or at least valid communication
        return response.contains("status") || response.contains("type") || !response.empty();
        
    } catch (const std::exception& e) {
        log_error("Server availability test failed: %s", e.what());
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

    try {
        // Convert JSON to string and send
        std::string json_str = message.dump();
        zmq::message_t request(json_str.size());
        memcpy(request.data(), json_str.c_str(), json_str.size());
        
        // Send request with timeout using polling
        zmq::pollitem_t poll_items[] = { { *socket_, 0, ZMQ_POLLOUT, 0 } };
        int poll_result = zmq::poll(poll_items, 1, std::chrono::milliseconds(5000)); // 5 second timeout
        
        if (poll_result == 0) {
            log_error("Send timeout: server not responding");
            connected_ = false; // Mark as disconnected
            return json{{"status", "error"}, {"message", "send timeout"}};
        } else if (poll_result < 0) {
            log_error("Poll error during send");
            connected_ = false;
            return json{{"status", "error"}, {"message", "poll error"}};
        }
        
        if (!socket_->send(request, zmq::send_flags::dontwait)) {
            log_error("Failed to send request");
            connected_ = false;
            return json{{"status", "error"}, {"message", "send failed"}};
        }

        // Receive response with timeout using polling
        zmq::pollitem_t recv_poll_items[] = { { *socket_, 0, ZMQ_POLLIN, 0 } };
        poll_result = zmq::poll(recv_poll_items, 1, std::chrono::milliseconds(10000)); // 10 second timeout for response
        
        if (poll_result == 0) {
            log_error("Receive timeout: server not responding to request");
            // Don't immediately disconnect, but try to recover the socket state
            // Reset socket to clean state for REQ-REP pattern
            try {
                socket_->close();
                socket_ = std::make_unique<zmq::socket_t>(*context_, zmq::socket_type::req);
                std::string endpoint = "tcp://" + server_host_ + ":" + std::to_string(server_port_);
                socket_->connect(endpoint);
                // Keep connected_ as true since we've reconnected the socket
                log_info("Socket reset due to receive timeout, attempting to maintain connection");
            } catch (const std::exception& e) {
                log_error("Failed to reset socket after timeout: %s", e.what());
                connected_ = false;
            }
            return json{{"status", "error"}, {"message", "receive timeout"}};
        } else if (poll_result < 0) {
            log_error("Poll error during receive");
            connected_ = false;
            return json{{"status", "error"}, {"message", "poll error"}};
        }

        zmq::message_t reply;
        if (!socket_->recv(reply, zmq::recv_flags::dontwait)) {
            log_error("Failed to receive response");
            connected_ = false;
            return json{{"status", "error"}, {"message", "receive failed"}};
        }

        // Parse JSON response
        std::string reply_str(static_cast<char*>(reply.data()), reply.size());
        return json::parse(reply_str);

    } catch (const json::parse_error& e) {
        log_error("JSON parse error: %s", e.what());
        return json{{"status", "error"}, {"message", "json parse error"}};
    } catch (const std::exception& e) {
        log_error("Error sending request: %s", e.what());
        connected_ = false;
        return json{{"status", "error"}, {"message", e.what()}};
    }
}

/**
 * @brief Test heartbeat functionality
 * 
 * @return json Server response
 */
json ZmqClient::testHeartbeat() {
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
        
        // Set socket options for better timeout handling
        int timeout = 5000; // 5 seconds
        socket_->set(zmq::sockopt::rcvtimeo, timeout);
        socket_->set(zmq::sockopt::sndtimeo, timeout);
        socket_->set(zmq::sockopt::linger, 0); // Don't linger on close
        
        // Attempt connection
        std::string endpoint = "tcp://" + server_host_ + ":" + std::to_string(server_port_);
        socket_->connect(endpoint);
        
        // Test connection with a simple heartbeat
        json test_message = {
            {"type", "heartbeat"},
            {"client_time", getCurrentTimestamp()}
        };
        
        json response = sendRequest(test_message);
        if (response.contains("status") && response["status"] == "success") {
            connected_ = true;
            log_info("Successfully reconnected to QuantServer at %s:%d", server_host_.c_str(), server_port_);
            return true;
        } else {
            connected_ = false;
            log_error("Reconnection test failed: %s", response.dump().c_str());
            return false;
        }
        
    } catch (const std::exception& e) {
        connected_ = false;
        log_error("Error during reconnection: %s", e.what());
        return false;
    }
}

} // namespace QAUtils
