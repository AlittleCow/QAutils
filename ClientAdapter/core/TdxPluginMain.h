#ifndef __TDX_PLUGIN_MAIN_H__
#define __TDX_PLUGIN_MAIN_H__

#include "TdxFunctionRegistry.h"

#ifdef __cplusplus
extern "C"
{
#endif

/**
 * @brief Main TDX plugin registration function
 * 
 * This is the entry point that TDX calls to get the list of available functions.
 * It follows the standard TDX plugin interface specification.
 * 
 * @param pInfo Pointer to function info array pointer
 * @return TRUE if registration succeeded, FALSE otherwise
 */
__declspec(dllexport) BOOL RegisterTdxFunc(PluginTCalcFuncInfo** pInfo);

#ifdef __cplusplus
}
#endif

/**
 * @brief TDX Plugin Manager
 * 
 * This class manages the plugin lifecycle and provides initialization
 * and cleanup functionality for the TDX plugin system.
 */
class TdxPluginManager
{
public:
    /**
     * @brief Initialize the plugin system
     * 
     * This method registers all available functions and sets up
     * the plugin for use by TDX.
     * 
     * @return true if initialization succeeded
     */
    static bool Initialize();

    /**
     * @brief Cleanup the plugin system
     * 
     * This method unregisters all functions and cleans up resources.
     */
    static void Cleanup();

    /**
     * @brief Get plugin information
     * @return String containing plugin details
     */
    static std::string GetPluginInfo();

    /**
     * @brief Register all built-in functions
     * 
     * This method registers the default set of functions provided
     * by this plugin. It can be overridden to register custom functions.
     */
    static void RegisterBuiltInFunctions();

    /**
     * @brief Check if plugin is initialized
     * @return true if plugin is ready for use
     */
    static bool IsInitialized();

private:
    /** @brief Plugin initialization flag */
    static bool s_initialized;
};

#endif // __TDX_PLUGIN_MAIN_H__ 