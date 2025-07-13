cmake_minimum_required(VERSION 3.10)

# Enable vcpkg for 32-bit build
# Set vcpkg toolchain file - MUST be set before project()
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
    set(CMAKE_TOOLCHAIN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/../../vcpkg/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "Vcpkg toolchain file")
    message(STATUS "Using vcpkg toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# Force 32-bit build by setting vcpkg target triplet
if(NOT DEFINED VCPKG_TARGET_TRIPLET)
    set(VCPKG_TARGET_TRIPLET "x86-windows" CACHE STRING "Vcpkg target triplet")
endif()

# Force 32-bit architecture
set(CMAKE_GENERATOR_PLATFORM "Win32")
set(CMAKE_SIZEOF_VOID_P 4)

# Clear environment variables that might interfere with package finding
# unset(ENV{CMAKE_PREFIX_PATH})
# unset(ENV{CMAKE_MODULE_PATH})

project(QAUtilsKTPlugin VERSION 1.0.0)

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

# Define source files for KT Plugin
# Only include files that currently exist for basic testing
# Find required packages first to determine ENABLE_SERVER_FUNCTIONS
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

# Find ZeroMQ package
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(ZMQ QUIET libzmq)
endif()

if(NOT ZMQ_FOUND)
    find_package(zeromq CONFIG QUIET)
    if(zeromq_FOUND)
        set(ZMQ_FOUND TRUE)
        set(ZMQ_LIBRARIES libzmq)
        message(STATUS "Found ZeroMQ via vcpkg")
    endif()
endif()

if(NOT ZMQ_FOUND)
    message(STATUS "ZeroMQ not found, server functions will be disabled")
    set(ENABLE_SERVER_FUNCTIONS OFF)
else()
    message(STATUS "Found ZeroMQ, enabling server functions")
    set(ENABLE_SERVER_FUNCTIONS ON)
endif()

# Now define headers and sources after ENABLE_SERVER_FUNCTIONS is set
set(HEADERS
    core/KTFunctionBase.h
    core/KTFunctionRegistry.h
    core/KTPluginMain.h
    module/KTCommonFunc.h
    # utils/KTUtilities.h          # Will be added when implemented
    utils/log.h
)

# Add server-related headers only if server functions are enabled
if(ENABLE_SERVER_FUNCTIONS)
    list(APPEND HEADERS
        module/KTServerFunc.h
        module/KTServerApi.h
    )
endif()

set(SOURCES
    core/KTFunctionBase.cpp
    core/KTFunctionRegistry.cpp
    core/KTPluginMain.cpp
    module/KTCommonFunc.cpp
    # utils/KTUtilities.cpp        # Will be added when implemented
    utils/log.cpp
)

# Add server-related sources only if server functions are enabled
if(ENABLE_SERVER_FUNCTIONS)
    list(APPEND SOURCES
        module/KTServerFunc.cpp
        module/KTServerApi.cpp
    )
endif()

# Find cppzmq for C++ bindings (provides zmq.hpp)
if(ENABLE_SERVER_FUNCTIONS)
    find_package(cppzmq CONFIG QUIET)
    if(cppzmq_FOUND)
        message(STATUS "Found cppzmq via vcpkg")
    else()
        message(STATUS "cppzmq not found, disabling server functions")
        set(ENABLE_SERVER_FUNCTIONS OFF)
    endif()
endif()

# Find nlohmann_json - try CMake config first (vcpkg style)
if(ENABLE_SERVER_FUNCTIONS)
    find_package(nlohmann_json CONFIG QUIET)
    if(nlohmann_json_FOUND)
        message(STATUS "Found nlohmann_json via vcpkg CMake config")
    else()
        message(STATUS "nlohmann_json not found, disabling server functions")
        set(ENABLE_SERVER_FUNCTIONS OFF)
    endif()
endif()

# Create the DLL for KT Plugin
add_library(QAUtilsKTPlugin SHARED ${HEADERS} ${SOURCES})

# Set DLL properties
set_target_properties(QAUtilsKTPlugin PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    WINDOWS_EXPORT_ALL_SYMBOLS ON
)

# Link system libraries
if(WIN32)
    target_link_libraries(QAUtilsKTPlugin
        kernel32
        user32
    )
else()
    # Basic libraries for non-Windows
endif()

# Link ZeroMQ libraries only if server functions are enabled
if(ENABLE_SERVER_FUNCTIONS)
    if(ZMQ_LIBRARIES)
        target_link_libraries(QAUtilsKTPlugin ${ZMQ_LIBRARIES})
    endif()
    if(cppzmq_FOUND)
        target_link_libraries(QAUtilsKTPlugin cppzmq)
    endif()
    if(nlohmann_json_FOUND)
        target_link_libraries(QAUtilsKTPlugin nlohmann_json::nlohmann_json)
    endif()
endif()

# Include directories
target_include_directories(QAUtilsKTPlugin PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/core
    ${CMAKE_CURRENT_SOURCE_DIR}/module
    ${CMAKE_CURRENT_SOURCE_DIR}/utils
    "${CMAKE_CURRENT_SOURCE_DIR}/../../vcpkg/installed/${VCPKG_TARGET_TRIPLET}/include"
)

# Add cppzmq include directory if found manually
if(CPPZMQ_INCLUDE_DIR AND NOT cppzmq_FOUND)
    target_include_directories(QAUtilsKTPlugin PRIVATE ${CPPZMQ_INCLUDE_DIR})
    message(STATUS "Added cppzmq include directory: ${CPPZMQ_INCLUDE_DIR}")
endif()

# Add compile definitions based on server functions availability
if(ENABLE_SERVER_FUNCTIONS)
    target_compile_definitions(QAUtilsKTPlugin PRIVATE ENABLE_SERVER_FUNCTIONS=1)
    message(STATUS "Server functions enabled")
else()
    target_compile_definitions(QAUtilsKTPlugin PRIVATE ENABLE_SERVER_FUNCTIONS=0)
    message(STATUS "Server functions disabled - building basic plugin only")
endif()

# Preprocessor definitions for KT Plugin
target_compile_definitions(QAUtilsKTPlugin PRIVATE
    KTPLUGIN_EXPORTS
    _WINDLL
)

# Install rules
install(TARGETS QAUtilsKTPlugin
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(FILES ${HEADERS}
    DESTINATION include/QAUtilsKTPlugin
)

# Print configuration information
message(STATUS "=== QAUtils KT Plugin Configuration ===")
message(STATUS "Version: ${PROJECT_VERSION}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "=====================================")

# Add test subdirectory
add_subdirectory(test)

# Tests are defined in test/CMakeLists.txt

# Package configuration
set(CPACK_PACKAGE_NAME "QAUtilsKTPlugin")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Object-Oriented KT Plugin Framework")
set(CPACK_PACKAGE_VENDOR "QAUtils Development Team")
set(CPACK_PACKAGE_CONTACT "qautils@example.com")

if(WIN32)
    set(CPACK_GENERATOR "ZIP")
else()
    set(CPACK_GENERATOR "TGZ")
endif()

include(CPack)

# Add post-build step to copy DLL to KT directory (需要根据实际KT安装路径修改)
# add_custom_command(TARGET QAUtilsKTPlugin POST_BUILD
#     COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:QAUtilsKTPlugin> "C:/KT/plugins/"
#     COMMENT "Copying QAUtilsKTPlugin.dll to KT plugin directory"
# )