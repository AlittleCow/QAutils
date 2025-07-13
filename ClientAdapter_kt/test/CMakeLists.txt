# Test CMakeLists.txt for KT Plugin
cmake_minimum_required(VERSION 3.10)

# Test executable for basic functionality
add_executable(test_basic test_basic.cpp)

# Link with the main library sources (since we're building a static test)
target_sources(test_basic PRIVATE
    ../core/KTFunctionBase.cpp
    ../utils/log.cpp
)

# Technical indicators test executable
add_executable(test_technical_indicators test_technical_indicators.cpp)

# Link with all necessary sources for technical indicators test
target_sources(test_technical_indicators PRIVATE
    ../core/KTFunctionBase.cpp
    ../core/KTFunctionRegistry.cpp
    ../core/KTPluginMain.cpp
    ../module/KTCommonFunc.cpp
    ../utils/log.cpp
)

# Include directories
target_include_directories(test_basic PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/..
    ${CMAKE_CURRENT_SOURCE_DIR}/../core
    ${CMAKE_CURRENT_SOURCE_DIR}/../utils
)

target_include_directories(test_technical_indicators PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/..
    ${CMAKE_CURRENT_SOURCE_DIR}/../core
    ${CMAKE_CURRENT_SOURCE_DIR}/../module
    ${CMAKE_CURRENT_SOURCE_DIR}/../utils
)

# Compiler definitions
target_compile_definitions(test_basic PRIVATE
    _CRT_SECURE_NO_WARNINGS
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)

target_compile_definitions(test_technical_indicators PRIVATE
    _CRT_SECURE_NO_WARNINGS
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)

# Set C++ standard
set_target_properties(test_basic PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

set_target_properties(test_technical_indicators PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

# Add tests
enable_testing()
add_test(NAME BasicInfrastructureTest COMMAND test_basic)
add_test(NAME TechnicalIndicatorsTest COMMAND test_technical_indicators)

# Set test properties
set_tests_properties(BasicInfrastructureTest PROPERTIES
    TIMEOUT 30
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

set_tests_properties(TechnicalIndicatorsTest PROPERTIES
    TIMEOUT 60
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

# Print test information
message(STATUS "Test executables: test_basic, test_technical_indicators")
message(STATUS "Test working directory: ${CMAKE_CURRENT_BINARY_DIR}")