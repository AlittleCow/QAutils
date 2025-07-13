#ifndef __KT_PLUGIN_MAIN_H__
#define __KT_PLUGIN_MAIN_H__

#include "KTFunctionRegistry.h"

#ifdef __cplusplus
extern "C"
{
#endif

/**
 * @brief Main KT plugin registration function
 * 
 * This is the entry point that KT calls to get the list of available functions.
 * It follows the standard KT plugin interface specification.
 * Uses the dynamic function registry to build the function table at runtime.
 * This allows for flexible function registration and management.
 * 
 * @param pInfo Pointer to function info array pointer
 * @return TRUE if registration succeeded, FALSE otherwise
 */
__declspec(dllexport) BOOL RegisterKTFunc(KTFuncInfo** pInfo);

/**
 * @brief Get function count
 * 
 * Returns the number of functions available in this plugin.
 * 
 * @return Number of functions
 */
__declspec(dllexport) int GetFunctionCount();

/**
 * @brief Get function information by index
 * 
 * Returns detailed information about a specific function.
 * 
 * @param nIndex Function index (0-based)
 * @param pFuncInfo Pointer to receive function information
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL GetFunctionInfo(int nIndex, KTFuncInfo* pFuncInfo);

/**
 * @brief Call function by index
 * 
 * Executes a specific function with the provided calculation data.
 * 
 * @param nIndex Function index (0-based)
 * @param pCalcInfo Pointer to calculation information
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL CallFunction(int nIndex, CALCINFO* pCalcInfo);



// =============================================================================
// Direct Function Exports for KT Trading Platform
// =============================================================================
// These are thin wrapper functions that KT can directly call by name
// They internally dispatch to our framework functions

/**
 * @brief Simple Moving Average - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_SMA(CALCINFO* pCalcInfo);

/**
 * @brief Exponential Moving Average - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_EMA(CALCINFO* pCalcInfo);

/**
 * @brief MACD Indicator - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_MACD(CALCINFO* pCalcInfo);

/**
 * @brief RSI Indicator - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_RSI(CALCINFO* pCalcInfo);

// Server functions (if enabled)
#if ENABLE_SERVER_FUNCTIONS
/**
 * @brief Server SMA - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_SMA_SERVER(CALCINFO* pCalcInfo);

/**
 * @brief Server EMA - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_EMA_SERVER(CALCINFO* pCalcInfo);

/**
 * @brief Server RSI - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_RSI_SERVER(CALCINFO* pCalcInfo);

/**
 * @brief Server MACD - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_MACD_SERVER(CALCINFO* pCalcInfo);

// =============================================================================
// Server Management Functions - Direct Exports
// =============================================================================

/**
 * @brief Server Connect - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_SERVER_CONNECT(CALCINFO* pCalcInfo);

/**
 * @brief Server Disconnect - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_SERVER_DISCONNECT(CALCINFO* pCalcInfo);

/**
 * @brief Server Status - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_SERVER_STATUS(CALCINFO* pCalcInfo);

/**
 * @brief Server Send K-Bar - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_SERVER_SEND_KBAR(CALCINFO* pCalcInfo);

/**
 * @brief Server Call API - Direct Export
 * @param pCalcInfo Calculation information structure
 * @return TRUE if successful, FALSE otherwise
 */
__declspec(dllexport) BOOL KT_SERVER_CALL_API(CALCINFO* pCalcInfo);

#endif

#ifdef __cplusplus
}
#endif

/**
 * @brief KT Plugin Manager
 * 
 * This class manages the plugin lifecycle and provides initialization
 * and cleanup functionality for the KT plugin system.
 */
class KTPluginManager
{
public:
    /**
     * @brief Initialize the plugin system
     * 
     * This method registers all available functions and sets up
     * the plugin for use by KT.
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
     * @brief Check if plugin system is initialized
     * @return true if initialized
     */
    static bool IsInitialized();

    /**
     * @brief Get plugin information string
     * @return Plugin information as formatted string
     */
    static std::string GetPluginInfo();

private:
    /**
     * @brief Register all built-in functions
     */
    static void RegisterBuiltInFunctions();

    static bool s_initialized;  ///< Initialization status flag
};

#endif // __KT_PLUGIN_MAIN_H__