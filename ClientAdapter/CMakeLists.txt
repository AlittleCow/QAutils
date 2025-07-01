cmake_minimum_required(VERSION 3.10)

# Set vcpkg toolchain file - MUST be set before project()
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
    set(CMAKE_TOOLCHAIN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/../../vcpkg/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "Vcpkg toolchain file")
    message(STATUS "Using vcpkg toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# Set vcpkg target triplet for Win32
if(NOT DEFINED VCPKG_TARGET_TRIPLET)
    set(VCPKG_TARGET_TRIPLET "x86-windows" CACHE STRING "Vcpkg target triplet")
endif()

# Clear environment variables that might interfere with package finding
unset(ENV{CMAKE_PREFIX_PATH})
unset(ENV{CMAKE_MODULE_PATH})

project(QAUtilsTdxPlugin VERSION 1.0.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Platform and architecture information
message(STATUS "Target architecture: ${CMAKE_GENERATOR_PLATFORM}")
message(STATUS "System processor: ${CMAKE_SYSTEM_PROCESSOR}")
if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(STATUS "Building for 64-bit")
elseif(CMAKE_SIZEOF_VOID_P EQUAL 4)
    message(STATUS "Building for 32-bit")
endif()

# Set output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Compiler-specific options
if(MSVC)
    # MSVC specific options
    add_compile_options(/W4 /WX)
    # Suppress C4100 warning for unreferenced parameters (common in DllMain)
    add_compile_options(/wd4100)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
    add_compile_definitions(WIN32_LEAN_AND_MEAN)
    add_compile_definitions(NOMINMAX)
    
    # Enable debug information in release builds
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /Zi")
    set(CMAKE_EXE_LINKER_FLAGS_RELEASE "${CMAKE_EXE_LINKER_FLAGS_RELEASE} /DEBUG /OPT:REF /OPT:ICF")
else()
    # GCC/Clang options
    add_compile_options(-Wall -Wextra -Werror)
endif()

# Define source files
set(HEADERS
    core/ITdxFunction.h
    core/TdxFunctionBase.h
    core/TdxFunctionRegistry.h
    core/TdxPluginMain.h
    module/TdxCommonFunc.h
    module/ServerApi.h
    utils/TdxUtilities.h
    utils/log.h
)

set(SOURCES
    core/TdxFunctionBase.cpp
    core/TdxFunctionRegistry.cpp
    core/TdxPluginMain.cpp
    module/TdxCommonFunc.cpp
    module/ServerApi.cpp
    utils/TdxUtilities.cpp
    utils/log.cpp
)

# Find required packages
# Ensure we're using vcpkg packages by setting CMAKE_PREFIX_PATH
if(DEFINED VCPKG_TARGET_TRIPLET)
    message(STATUS "Using vcpkg triplet: ${VCPKG_TARGET_TRIPLET}")
endif()

# Clear any system-wide package paths that might interfere
set(CMAKE_IGNORE_PATH ${CMAKE_IGNORE_PATH} 
    "C:/Users/lhe/AppData/Local/miniconda3"
    "$ENV{CONDA_PREFIX}"
)

# Force vcpkg package paths to be used first
set(CMAKE_PREFIX_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../../vcpkg/installed/${VCPKG_TARGET_TRIPLET}" ${CMAKE_PREFIX_PATH})
message(STATUS "CMAKE_PREFIX_PATH: ${CMAKE_PREFIX_PATH}")

# Clear system CMAKE_MODULE_PATH to prevent interference
set(CMAKE_MODULE_PATH "")

find_package(ZeroMQ CONFIG REQUIRED)
if(ZeroMQ_FOUND)
    message(STATUS "Found ZeroMQ via vcpkg")
    get_target_property(ZMQ_LOCATION libzmq LOCATION)
    message(STATUS "ZeroMQ location: ${ZMQ_LOCATION}")
else()
    message(FATAL_ERROR "ZeroMQ not found. Please ensure it's installed with: vcpkg install zeromq:x86-windows")
endif()

# Find cppzmq for C++ bindings (provides zmq.hpp)
find_package(cppzmq CONFIG QUIET)
if(cppzmq_FOUND)
    message(STATUS "Found cppzmq via vcpkg")
else()
    message(WARNING "cppzmq not found. Trying to install it...")
    # Try to find zmq.hpp manually in vcpkg installed directory
    find_path(CPPZMQ_INCLUDE_DIR zmq.hpp
        PATHS "${CMAKE_CURRENT_SOURCE_DIR}/../../vcpkg/installed/${VCPKG_TARGET_TRIPLET}/include"
        NO_DEFAULT_PATH
    )
    if(CPPZMQ_INCLUDE_DIR)
        message(STATUS "Found zmq.hpp at: ${CPPZMQ_INCLUDE_DIR}")
    else()
        message(WARNING "zmq.hpp not found. You may need to install: vcpkg install cppzmq:x86-windows")
    endif()
endif()

# Find nlohmann_json - try CMake config first (vcpkg style)
find_package(nlohmann_json CONFIG REQUIRED)
if(nlohmann_json_FOUND)
    message(STATUS "Found nlohmann_json via vcpkg CMake config")
    get_target_property(JSON_LOCATION nlohmann_json::nlohmann_json INTERFACE_INCLUDE_DIRECTORIES)
    message(STATUS "nlohmann_json include dirs: ${JSON_LOCATION}")
else()
    message(FATAL_ERROR "nlohmann_json not found. Please ensure it's installed with: vcpkg install nlohmann-json:x86-windows")
endif()

# Create the DLL
add_library(QAUtilsTdxPlugin SHARED ${HEADERS} ${SOURCES})

# Set DLL properties
set_target_properties(QAUtilsTdxPlugin PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    WINDOWS_EXPORT_ALL_SYMBOLS ON
)

# Link system libraries
if(WIN32)
    target_link_libraries(QAUtilsTdxPlugin
        kernel32
        user32
        libzmq
    )
    # Link cppzmq if found
    if(cppzmq_FOUND)
        target_link_libraries(QAUtilsTdxPlugin cppzmq)
    endif()
else()
    target_link_libraries(QAUtilsTdxPlugin
        libzmq
    )
    if(cppzmq_FOUND)
        target_link_libraries(QAUtilsTdxPlugin cppzmq)
    endif()
endif()

# Include directories
target_include_directories(QAUtilsTdxPlugin PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/core
    ${CMAKE_CURRENT_SOURCE_DIR}/module
    ${CMAKE_CURRENT_SOURCE_DIR}/utils
    # Explicitly add vcpkg include directory for zmq.hpp
    "${CMAKE_CURRENT_SOURCE_DIR}/../../vcpkg/installed/${VCPKG_TARGET_TRIPLET}/include"
)

# Add cppzmq include directory if found manually
if(CPPZMQ_INCLUDE_DIR AND NOT cppzmq_FOUND)
    target_include_directories(QAUtilsTdxPlugin PRIVATE ${CPPZMQ_INCLUDE_DIR})
    message(STATUS "Added cppzmq include directory: ${CPPZMQ_INCLUDE_DIR}")
endif()

# Add nlohmann/json include directory if found
if(nlohmann_json_FOUND)
    target_link_libraries(QAUtilsTdxPlugin nlohmann_json::nlohmann_json)
elseif(JSON_LOCATION)
    target_include_directories(QAUtilsTdxPlugin PRIVATE ${JSON_LOCATION})
endif()

# Preprocessor definitions
target_compile_definitions(QAUtilsTdxPlugin PRIVATE
    TDXPLUGIN_EXPORTS
    _WINDLL
)

# Install rules
install(TARGETS QAUtilsTdxPlugin
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(FILES ${HEADERS}
    DESTINATION include/QAUtilsTdxPlugin
)

# Print configuration information
message(STATUS "=== QAUtils TDX Plugin Configuration ===")
message(STATUS "Version: ${PROJECT_VERSION}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "=====================================")

# Package configuration
set(CPACK_PACKAGE_NAME "QAUtilsTdxPlugin")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Object-Oriented TDX Plugin Framework")
set(CPACK_PACKAGE_VENDOR "QAUtils Development Team")
set(CPACK_PACKAGE_CONTACT "qautils@example.com")

if(WIN32)
    set(CPACK_GENERATOR "ZIP")
else()
    set(CPACK_GENERATOR "TGZ")
endif()

include(CPack)

# Add post-build step to copy DLL to TDX directory
add_custom_command(TARGET QAUtilsTdxPlugin POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:QAUtilsTdxPlugin> "C:/new_tdx/T0002/dlls/"
    COMMENT "Copying QAUtilsTdxPlugin.dll to TDX plugin directory"
) 