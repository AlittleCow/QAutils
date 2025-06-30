#include "TdxPluginMain.h"
#include "../test/TdxExampleFunctions.h"
#include "../utils/log.h"
#include <iostream>
#include <sstream>

// Static member initialization
bool TdxPluginManager::s_initialized = false;

/**
 * @brief Main TDX plugin registration function (C interface)
 * 
 * This is the entry point called by TDX to register plugin functions.
 * It initializes the plugin if needed and returns the function array.
 * 
 * @param pInfo Pointer to function info array pointer
 * @return TRUE if registration succeeded
 */
BOOL RegisterTdxFunc(PluginTCalcFuncInfo** pInfo)
{
    try
    {
        // Initialize plugin if not already done
        if (!TdxPluginManager::IsInitialized())
        {
            if (!TdxPluginManager::Initialize())
            {
                log_debug("Failed to initialize TDX plugin");
                return FALSE;
            }
        }

        // Get registry instance
        auto& registry = TdxFunctionRegistry::GetInstance();
        
        // Check if we have any functions registered
        if (registry.GetFunctionCount() == 0)
        {
            log_debug("No functions registered in TDX plugin");
            return FALSE;
        }

        // Return the function array
        if (pInfo != nullptr)
        {
            *pInfo = registry.GetCFunctionInfoArray();
            
            log_debug("TDX Plugin registered %d functions successfully", registry.GetFunctionCount());
            
            return TRUE;
        }
        
        return FALSE;
    }
    catch (const std::exception& e)
    {
        log_debug("Exception in RegisterTdxFunc: %s", e.what());
        return FALSE;
    }
    catch (...)
    {
        log_debug("Unknown exception in RegisterTdxFunc");
        return FALSE;
    }
}

// ============================================================================
// TdxPluginManager Implementation
// ============================================================================

/**
 * @brief Initialize the plugin system
 * @return true if initialization succeeded
 */
bool TdxPluginManager::Initialize()
{
    if (s_initialized)
    {
        return true;
    }

    try
    {
        log_debug("Initializing TDX Plugin System...");
        
        // Get registry instance and initialize
        auto& registry = TdxFunctionRegistry::GetInstance();
        registry.InitializeDefaultFunctions();
        
        // Register built-in functions
        RegisterBuiltInFunctions();
        
        s_initialized = true;
        
        log_debug("TDX Plugin System initialized successfully");
        log_debug("%s", registry.GetRegistryInfo().c_str());
        
        return true;
    }
    catch (const std::exception& e)
    {
        log_debug("Failed to initialize TDX plugin: %s", e.what());
        return false;
    }
    catch (...)
    {
        log_debug("Unknown error during TDX plugin initialization");
        return false;
    }
}

/**
 * @brief Cleanup the plugin system
 */
void TdxPluginManager::Cleanup()
{
    if (!s_initialized)
    {
        return;
    }

    try
    {
        log_debug("Cleaning up TDX Plugin System...");
        
        // Clear all registered functions
        auto& registry = TdxFunctionRegistry::GetInstance();
        registry.Clear();
        
        s_initialized = false;
        
        log_debug("TDX Plugin System cleaned up successfully");
    }
    catch (const std::exception& e)
    {
        log_debug("Error during TDX plugin cleanup: %s", e.what());
    }
    catch (...)
    {
        log_debug("Unknown error during TDX plugin cleanup");
    }
}

/**
 * @brief Get plugin information
 * @return String containing plugin details
 */
std::string TdxPluginManager::GetPluginInfo()
{
    std::ostringstream oss;
    oss << "=== TDX Plugin Information ===\n";
    oss << "Plugin Name: QAUtils TDX Plugin\n";
    oss << "Version: 1.0.0\n";
    oss << "Author: QAUtils Development Team\n";
    oss << "Description: Object-Oriented TDX Plugin Framework\n";
    oss << "Initialized: " << (s_initialized ? "Yes" : "No") << "\n";
    
    if (s_initialized)
    {
        auto& registry = TdxFunctionRegistry::GetInstance();
        oss << "\n" << registry.GetRegistryInfo();
    }
    
    oss << "==============================\n";
    return oss.str();
}

/**
 * @brief Register all built-in functions
 */
void TdxPluginManager::RegisterBuiltInFunctions()
{
    auto& registry = TdxFunctionRegistry::GetInstance();
    
    try
    {
        log_debug("Registering built-in functions...");
        
        // Register example functions
        bool success = true;
        
        success &= registry.RegisterFunction(std::make_shared<SequenceFunction>());
        success &= registry.RegisterFunction(std::make_shared<AverageFunction>());
        success &= registry.RegisterFunction(std::make_shared<SimpleMovingAverageFunction>());
        success &= registry.RegisterFunction(std::make_shared<ExponentialMovingAverageFunction>());
        success &= registry.RegisterFunction(std::make_shared<DebugControlFunction>());
        
        if (success)
        {
            log_debug("All built-in functions registered successfully");
        }
        else
        {
            log_debug("Some built-in functions failed to register");
        }
    }
    catch (const std::exception& e)
    {
        log_debug("Exception while registering built-in functions: %s", e.what());
    }
    catch (...)
    {
        log_debug("Unknown exception while registering built-in functions");
    }
}

/**
 * @brief Check if plugin is initialized
 * @return true if plugin is ready
 */
bool TdxPluginManager::IsInitialized()
{
    return s_initialized;
}

// ============================================================================
// DLL Entry Point (Optional)
// ============================================================================

#ifdef _WIN32
#include <windows.h>

/**
 * @brief DLL entry point
 * 
 * This function is called when the DLL is loaded/unloaded by the system.
 * It provides automatic initialization and cleanup.
 * 
 * @param hinstDLL Handle to DLL module
 * @param fdwReason Reason for calling function
 * @param lpvReserved Reserved parameter
 * @return TRUE to indicate success
 */
BOOL APIENTRY DllMain(HMODULE hinstDLL, DWORD fdwReason, LPVOID lpvReserved)
{
    switch (fdwReason)
    {
    case DLL_PROCESS_ATTACH:
        // Initialize logging
        log_init();
        log_set_level(LOG_DEBUG);
        
        // DLL is being loaded
        log_debug("TDX Plugin DLL loaded");
        break;
        
    case DLL_PROCESS_DETACH:
        // DLL is being unloaded
        TdxPluginManager::Cleanup();
        log_debug("TDX Plugin DLL unloaded");
        
        // Close logging
        log_close();
        break;
        
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
        break;
    }
    
    return TRUE;
}

#endif // _WIN32 