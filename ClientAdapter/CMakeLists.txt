cmake_minimum_required(VERSION 3.10)
project(QAUtilsTdxPlugin VERSION 1.0.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

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
    utils/TdxUtilities.h
    utils/log.h
)

set(SOURCES
    core/TdxFunctionBase.cpp
    core/TdxFunctionRegistry.cpp
    core/TdxPluginMain.cpp
    module/TdxCommonFunc.cpp
    utils/TdxUtilities.cpp
    utils/log.cpp
)

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
    )
endif()

# Include directories
target_include_directories(QAUtilsTdxPlugin PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/core
    ${CMAKE_CURRENT_SOURCE_DIR}/module
    ${CMAKE_CURRENT_SOURCE_DIR}/utils
)

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