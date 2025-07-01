#include "ServerApi.h"
#include <iostream>

using namespace QAUtils;

/**
 * @brief Simple test to demonstrate ZmqClient functionality
 * 
 * This test will work even without dependencies installed,
 * showing clear error messages about what's missing.
 */
int main() {
    std::cout << "=== ZmqClient Simple Test ===" << std::endl;
    std::cout << "This test demonstrates the ZmqClient class functionality." << std::endl;
    std::cout << "Even without dependencies, it will show what's needed." << std::endl;
    std::cout << std::endl;

    // Create client instance
    ZmqClient client("localhost", 5555);
    
    // Check dependency status
    std::cout << "=== Dependency Status ===" << std::endl;
    std::cout << "Dependencies available: " << (client.areDependenciesAvailable() ? "YES" : "NO") << std::endl;
    std::cout << std::endl;
    std::cout << client.getDependencyStatus() << std::endl;
    std::cout << std::endl;

    if (!client.areDependenciesAvailable()) {
        std::cout << "=== Testing Error Responses ===" << std::endl;
        std::cout << "Since dependencies are missing, all operations will return error responses:" << std::endl;
        std::cout << std::endl;

        // Test heartbeat (will show error)
        std::cout << "Testing heartbeat..." << std::endl;
        auto heartbeat_response = client.testHeartbeat();
        std::cout << "Response: " << heartbeat_response.dump(2) << std::endl;
        std::cout << std::endl;

        // Test connection attempt
        std::cout << "Testing connection..." << std::endl;
        bool connected = client.connect();
        std::cout << "Connection result: " << (connected ? "SUCCESS" : "FAILED") << std::endl;
        std::cout << "Is connected: " << (client.isConnected() ? "YES" : "NO") << std::endl;
        std::cout << std::endl;

        std::cout << "=== Instructions to Enable Full Functionality ===" << std::endl;
        std::cout << "To make this client fully functional:" << std::endl;
        std::cout << "1. Install ZeroMQ C++ bindings (cppzmq)" << std::endl;
        std::cout << "2. Install nlohmann/json library" << std::endl;
        std::cout << "3. Compile with proper flags and linking" << std::endl;
        std::cout << std::endl;
        std::cout << "Example compilation (when dependencies are installed):" << std::endl;
        std::cout << "g++ -std=c++17 -DZMQ_AVAILABLE -DJSON_AVAILABLE \\" << std::endl;
        std::cout << "    ServerApi.cpp simple_test.cpp \\" << std::endl;
        std::cout << "    -lzmq -o simple_test" << std::endl;
        std::cout << std::endl;
    } else {
        std::cout << "=== Full Functionality Test ===" << std::endl;
        std::cout << "Dependencies are available! Testing full functionality..." << std::endl;
        std::cout << std::endl;

        // Test connection
        std::cout << "Attempting to connect to server..." << std::endl;
        if (client.connect()) {
            std::cout << "Connected successfully!" << std::endl;
            
            // Test server availability first
            std::cout << "Testing server availability..." << std::endl;
            if (client.testServerAvailability()) {
                std::cout << "Server is responding to requests!" << std::endl;
                
                // Test heartbeat
                std::cout << "Testing heartbeat..." << std::endl;
                auto heartbeat_response = client.testHeartbeat();
                std::cout << "Heartbeat response: " << heartbeat_response.dump(2) << std::endl;
                
                // Test server info
                std::cout << "Getting server info..." << std::endl;
                auto server_info = client.getServerInfo();
                std::cout << "Server info: " << server_info.dump(2) << std::endl;
                
            } else {
                std::cout << "Server is not responding to requests." << std::endl;
                std::cout << "This could mean:" << std::endl;
                std::cout << "1. The QuantServer is not running" << std::endl;
                std::cout << "2. The server is running but not responding to heartbeat messages" << std::endl;
                std::cout << "3. There's a network connectivity issue" << std::endl;
                std::cout << std::endl;
                std::cout << "Attempting heartbeat anyway to see the error..." << std::endl;
                auto heartbeat_response = client.testHeartbeat();
                std::cout << "Heartbeat response: " << heartbeat_response.dump(2) << std::endl;
            }
            
        } else {
            std::cout << "Failed to connect to server." << std::endl;
            std::cout << "Make sure the Python QuantServer is running on localhost:5555" << std::endl;
            std::cout << std::endl;
            std::cout << "To start the server, you typically need to:" << std::endl;
            std::cout << "1. Navigate to the server directory" << std::endl;
            std::cout << "2. Run: python quantserver.py" << std::endl;
            std::cout << "3. Ensure the server is listening on port 5555" << std::endl;
        }
    }

    std::cout << "=== Test Complete ===" << std::endl;
    return 0;
} 