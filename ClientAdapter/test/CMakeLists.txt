cmake_minimum_required(VERSION 3.15)
project(ZmqClient)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Use the same package finding approach as parent CMakeLists.txt
# ZeroMQ and nlohmann_json should already be found by parent

# Create the library
add_library(ZmqClient STATIC 
    ../module/ServerApi.cpp
    ../utils/log.cpp
)

# Link libraries - use the same targets as parent
target_link_libraries(ZmqClient 
    libzmq
    nlohmann_json::nlohmann_json
)

# Include directories - inherit from parent
target_include_directories(ZmqClient PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/../module  # For ServerApi.h
    ${CMAKE_CURRENT_SOURCE_DIR}/../utils   # For log.h
)

# Create the example executable
add_executable(example_usage
    example_usage.cpp
)

# Add include directories for example_usage
target_include_directories(example_usage PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../module  # For ServerApi.h
)

# Link the example with the library
target_link_libraries(example_usage
    ZmqClient
    libzmq
    nlohmann_json::nlohmann_json
)

# Create the simple test executable
add_executable(simple_test
    simple_test.cpp
)

# Add include directories for simple_test
target_include_directories(simple_test PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../module  # For ServerApi.h
)

# Link the simple test with the library
target_link_libraries(simple_test
    ZmqClient
    libzmq
    nlohmann_json::nlohmann_json
)

# Installation (optional)
install(TARGETS ZmqClient example_usage simple_test
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(FILES ../module/ServerApi.h
    DESTINATION include
) 