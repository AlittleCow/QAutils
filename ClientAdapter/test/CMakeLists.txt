cmake_minimum_required(VERSION 3.15)
project(ZmqClient)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(PkgConfig REQUIRED)

# Find ZeroMQ
pkg_check_modules(ZMQ REQUIRED libzmq)

# Find nlohmann_json
find_package(nlohmann_json REQUIRED)

# Include directories
include_directories(${ZMQ_INCLUDE_DIRS})

# Create the library
add_library(ZmqClient STATIC 
    ServerApi.cpp
)

# Link libraries
target_link_libraries(ZmqClient 
    ${ZMQ_LIBRARIES}
    nlohmann_json::nlohmann_json
)

# Set compile flags
target_compile_options(ZmqClient PRIVATE ${ZMQ_CFLAGS_OTHER})

# Create the example executable
add_executable(example_usage
    example_usage.cpp
)

# Link the example with the library
target_link_libraries(example_usage
    ZmqClient
    ${ZMQ_LIBRARIES}
    nlohmann_json::nlohmann_json
)

# Set compile flags for the example
target_compile_options(example_usage PRIVATE ${ZMQ_CFLAGS_OTHER})

# Installation (optional)
install(TARGETS ZmqClient
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(FILES ServerApi.h
    DESTINATION include
) 