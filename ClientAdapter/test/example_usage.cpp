#include "ServerApi.h"
#include <iostream>
#include <vector>

using namespace QAUtils;

/**
 * @brief Example usage of the ZmqClient class
 * 
 * This function demonstrates how to use all the features of the ZmqClient
 * that correspond to the Python example client functionality.
 */
void demonstrateZmqClient() {
    // Create client instance
    ZmqClient client("localhost", 5555);
    
    // Connect to server
    if (!client.connect()) {
        std::cerr << "Failed to connect to server" << std::endl;
        return;
    }

    try {
        // Test heartbeat
        std::cout << "\n=== Testing Heartbeat ===" << std::endl;
        auto heartbeat_response = client.testHeartbeat();
        std::cout << "Heartbeat response: " << heartbeat_response.dump(2) << std::endl;

        // Test single K-bar data
        std::cout << "\n=== Testing Single Kbar Data ===" << std::endl;
        KBarData single_kbar = {
            "AAPL",
            "2024-01-15T10:30:00",
            150.25,
            151.80,
            149.90,
            151.50,
            1000000
        };
        auto single_kbar_response = client.testSingleKBar(single_kbar);
        std::cout << "Single K-bar response: " << single_kbar_response.dump(2) << std::endl;

        // Test K-bar series
        std::cout << "\n=== Testing Kbar Series Data ===" << std::endl;
        std::vector<KBarData> kbar_series = {
            {"AAPL", "2024-01-15T10:00:00", 150.00, 150.50, 149.50, 150.25, 500000},
            {"AAPL", "2024-01-15T10:30:00", 150.25, 151.80, 149.90, 151.50, 1000000},
            {"AAPL", "2024-01-15T11:00:00", 151.50, 152.20, 151.00, 151.75, 750000}
        };
        auto series_response = client.testKBarSeries("AAPL", kbar_series);
        std::cout << "K-bar series response: " << series_response.dump(2) << std::endl;

        // Test API calls (indicators)
        std::cout << "\n=== Testing API Calls (Indicators) ===" << std::endl;
        std::vector<double> price_data = {100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 
                                         111, 110, 112, 114, 113, 115, 117, 116, 118, 120};
        
        std::vector<ApiRequest> api_requests = {
            {
                "Simple Moving Average",
                "sma",
                {{"data", price_data}, {"period", 5}},
                true
            },
            {
                "RSI",
                "rsi", 
                {{"data", price_data}, {"period", 14}},
                true
            },
            {
                "EMA",
                "ema",
                {{"data", price_data}, {"period", 10}},
                false  // This should be skipped
            }
        };
        auto api_response = client.testApiCalls(api_requests);
        std::cout << "API calls response: " << api_response.dump(2) << std::endl;

        // Test control messages
        std::cout << "\n=== Testing Control Messages ===" << std::endl;
        
        // Set a parameter
        std::cout << "Setting parameter..." << std::endl;
        auto set_param_response = client.setParameter("max_connections", 100);
        std::cout << "Set param response: " << set_param_response.dump(2) << std::endl;
        
        // Get the parameter back
        std::cout << "\nGetting parameter..." << std::endl;
        auto get_param_response = client.getParameter("max_connections");
        std::cout << "Get param response: " << get_param_response.dump(2) << std::endl;
        
        // Get server info
        std::cout << "\nGetting server info..." << std::endl;
        auto server_info_response = client.getServerInfo();
        std::cout << "Server info response: " << server_info_response.dump(2) << std::endl;
        
        // Get all parameters
        std::cout << "\nGetting all parameters..." << std::endl;
        auto all_params_response = client.getAllParameters();
        std::cout << "All params response: " << all_params_response.dump(2) << std::endl;

        // Test individual indicator methods
        std::cout << "\n=== Testing Individual Indicator Methods ===" << std::endl;
        
        // SMA
        auto sma_response = client.calculateSMA(price_data, 5);
        std::cout << "SMA response: " << sma_response.dump(2) << std::endl;
        std::cout << "\n=== All tests completed ===" << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error during execution: " << e.what() << std::endl;
    }

    // Client will automatically disconnect when destructor is called
}

/**
 * @brief Main function to run the ZmqClient demonstration
 * 
 * @return int Exit code
 */
int main() {
    std::cout << "ZmqClient C++ Example - Connecting to QuantServer" << std::endl;
    std::cout << "Make sure the Python QuantServer is running before executing this program." << std::endl;
    
    try {
        demonstrateZmqClient();
    } catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
} 