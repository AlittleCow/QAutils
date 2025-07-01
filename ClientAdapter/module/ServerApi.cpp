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
    : server_host_(server_host), server_port_(server_port), connected_(false) {
    context_ = std::make_unique<zmq::context_t>(1);
    socket_ = std::make_unique<zmq::socket_t>(*context_, zmq::socket_type::req);
}

/**
 * @brief Destroy the ZmqClient object and cleanup resources
 */
ZmqClient::~ZmqClient() {
    disconnect();
}

/**
 * @brief Connect to the QuantServer
 * 
 * @return true if connection successful, false otherwise
 */
bool ZmqClient::connect() {
    try {
        std::string endpoint = "tcp://" + server_host_ + ":" + std::to_string(server_port_);
        socket_->connect(endpoint);
        connected_ = true;
        std::cout << "Connected to QuantServer at " << server_host_ << ":" << server_port_ << std::endl;
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error connecting to server: " << e.what() << std::endl;
        connected_ = false;
        return false;
    }
}

/**
 * @brief Disconnect from the QuantServer
 */
void ZmqClient::disconnect() {
    if (connected_) {
        socket_->close();
        connected_ = false;
        std::cout << "Disconnected from QuantServer" << std::endl;
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
 * @brief Send a JSON request and receive response
 * 
 * @param message The JSON message to send
 * @return json The response from server, empty JSON on error
 */
json ZmqClient::sendRequest(const json& message) {
    if (!connected_) {
        std::cerr << "Client not connected to server" << std::endl;
        return json{};
    }

    try {
        // Convert JSON to string and send
        std::string json_str = message.dump();
        zmq::message_t request(json_str.size());
        memcpy(request.data(), json_str.c_str(), json_str.size());
        
        if (!socket_->send(request, zmq::send_flags::none)) {
            std::cerr << "Failed to send request" << std::endl;
            return json{};
        }

        // Receive response
        zmq::message_t reply;
        if (!socket_->recv(reply, zmq::recv_flags::none)) {
            std::cerr << "Failed to receive response" << std::endl;
            return json{};
        }

        // Parse JSON response
        std::string reply_str(static_cast<char*>(reply.data()), reply.size());
        return json::parse(reply_str);

    } catch (const std::exception& e) {
        std::cerr << "Error sending request: " << e.what() << std::endl;
        return json{};
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
 * @brief Test Bollinger Bands calculation
 * 
 * @param price_data Vector of price data
 * @param period Period for calculation
 * @param std_dev Standard deviation multiplier
 * @return json Server response
 */
json ZmqClient::testBollingerBands(const std::vector<double>& price_data, int period, double std_dev) {
    ApiRequest request = {
        "Bollinger Bands",
        "bollinger",
        {
            {"data", price_data},
            {"period", period},
            {"std_dev", std_dev}
        },
        true
    };
    return testApiCalls({request});
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
 * @brief Helper method to create RSI request
 * 
 * @param price_data Vector of price data
 * @param period Period for RSI calculation
 * @return json Server response
 */
json ZmqClient::calculateRSI(const std::vector<double>& price_data, int period) {
    ApiRequest request = {
        "RSI",
        "rsi",
        {
            {"data", price_data},
            {"period", period}
        },
        true
    };
    return testApiCalls({request});
}

/**
 * @brief Helper method to create EMA request
 * 
 * @param price_data Vector of price data
 * @param period Period for EMA calculation
 * @return json Server response
 */
json ZmqClient::calculateEMA(const std::vector<double>& price_data, int period) {
    ApiRequest request = {
        "EMA",
        "ema",
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

} // namespace QAUtils
