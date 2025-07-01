#include "TdxPluginMain.h"
#include "../utils/log.h"
#include "../module/TdxCommonFunc.h"
#include "../module/TdxServerFunc.h"
#include <iostream>
#include <sstream>

// Static assertions to ensure memory layout compatibility
static_assert(sizeof(PluginTCalcFuncInfo) == sizeof(unsigned short) + sizeof(pPluginFUNC), 
              "PluginTCalcFuncInfo structure size mismatch");
static_assert(alignof(PluginTCalcFuncInfo) <= 8, 
              "PluginTCalcFuncInfo alignment too large");

// Static member initialization
bool TdxPluginManager::s_initialized = false;

/**
 * @brief Example TDX function implementation
 * 
 * This demonstrates the proper way to implement a TDX function with the new design.
 * The C-style function contains all the calculation logic and is called directly by TDX.
 */
class TdxStubFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor - defines function metadata
     */
    TdxStubFunction()
        : TdxFunctionBase(999, "TdxStub", "Simple stub function for testing - copies input A to output",
                         "Example", 1, false)
    {
    }

    /**
     * @brief Get the C-style function pointer that TDX will call directly
     * @return Function pointer to our static wrapper function
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxStubWrapper;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=source data, pOut=destination, pInB/pInC=unused";
    }

private:
    /**
     * @brief Static C-style wrapper function - this is what TDX calls directly
     * 
     * This function contains all the actual calculation logic and uses the
     * utility macros for error handling and logging.
     * 
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Input array A
     * @param pInB Input array B (unused)
     * @param pInC Input array C (unused)
     */
    static void TdxStubWrapper(int nCount, float* pOut, float* pInA, float* pInB, float* pInC)
    {  
        // Initialize output array
        InitializeOutput(pOut, nCount, 0.0f);
        
        // Perform the calculation - simple copy from input A to output
        if (pInA && pOut)
        {
            if (SafeArrayCopy(pOut, pInA, nCount))
            {
                LogDebug("TdxStub", "Successfully copied " + std::to_string(nCount) + " values");
            }
            else
            {
                LogError("TdxStub", "Failed to copy array data");
            }
        }
        else
        {
            LogError("TdxStub", "Invalid input parameters - pInA or pOut is null");
        }
    }
};

/**
 * @brief Main TDX plugin registration function (C interface) - Dynamic Registry
 * 
 * This is the entry point called by TDX to register plugin functions.
 * Uses the dynamic function registry to build the function table at runtime.
 * This allows for flexible function registration and management.
 * 
 * @param pInfo Pointer to function info array pointer
 * @return TRUE if registration succeeded
 */
BOOL RegisterTdxFunc(PluginTCalcFuncInfo** pInfo)
{
    if (pInfo == NULL)
    {
        return FALSE;
    }

    if (*pInfo == NULL)
    {
        // Initialize the plugin system if not already done
        if (!TdxPluginManager::IsInitialized())
        {
            if (!TdxPluginManager::Initialize())
            {
                log_error("Failed to initialize TDX plugin system");
                return FALSE;
            }
        }
        
        // Get the dynamic function array from the registry
        auto& registry = TdxFunctionRegistry::GetInstance();
        *pInfo = registry.GetCFunctionInfoArray();
        
        if (*pInfo == NULL)
        {
            log_error("Failed to get function array from registry");
            return FALSE;
        }
        
        // Validate memory layout compatibility with TDX expectations
        if (!registry.ValidateMemoryLayout())
        {
            log_error("Function array memory layout validation failed");
            return FALSE;
        }
        
        size_t functionCount = registry.GetFunctionCount();
        log_debug("TDX Plugin registered %zu functions successfully (dynamic registry)", functionCount);
        log_debug("Memory layout validation passed - array is TDX-compatible");
        return TRUE;
    }

    return FALSE;
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
        RegisterTdxServerFunctions();
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

        success &= registry.RegisterFunction(std::make_shared<TdxStubFunction>());
        // Register common functions (Kbar API functions)
        success &= RegisterTdxCommonFunctions();
        
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