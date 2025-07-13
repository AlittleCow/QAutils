#include "KTPluginMain.h"
#include "KTFunctionRegistry.h"
#include "../module/KTCommonFunc.h"
#ifdef ENABLE_SERVER_FUNCTIONS
#include "../module/KTServerFunc.h"
#endif
#include "../utils/log.h"
#include <iostream>
#include <sstream>
#include <memory>
#include <stdexcept>

// Server function ID offset (must match KTServerFunc.cpp)
#ifdef ENABLE_SERVER_FUNCTIONS
constexpr int KT_SERVER_FUNCTION_ID_OFFSET = 3000;
#endif

// Static assertions to ensure memory layout compatibility
static_assert(sizeof(KTFuncInfo) >= sizeof(unsigned short) + sizeof(pKTFUNC), 
              "KTFuncInfo structure size too small");
static_assert(alignof(KTFuncInfo) <= 8, 
              "KTFuncInfo alignment too large");

// Static member initialization
bool KTPluginManager::s_initialized = false;

/**
 * @brief Example KT function implementation
 * 
 * This demonstrates the proper way to implement a KT function with the new design.
 * The C-style function contains all the calculation logic and is called directly by KT.
 */
class KTStubFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor - defines function metadata
     */
    KTStubFunction()
        : KTFunctionBase(999, "KTStub", "Simple stub function for testing - copies close prices to output",
                         "Example", 1, false, 1, false, false)
    {
    }

    /**
     * @brief Get the C-style function pointer
     * @return Function pointer for KT registration
     */
    pKTFUNC GetKTFunctionPointer() const override {
        return &KTStubWrapper;
    }

private:
    /**
     * @brief Static C-style function wrapper for KT
     * @param pCalcInfo Pointer to calculation information
     * @return TRUE if successful, FALSE otherwise
     */
    static BOOL KTStubWrapper(CALCINFO* pCalcInfo)
    {  
        // Validate input
        if (!KTFunctionBase::ValidateCALCINFOStatic(pCalcInfo, "KTStub")) {
            return FALSE;
        }
        
        // Initialize results
        KTFunctionBase::InitializeResults(pCalcInfo, 0.0f);
        
        // Simple copy operation: copy close prices to output
        for (int i = 0; i < static_cast<int>(pCalcInfo->nCount); ++i) {
            if (pCalcInfo->pData && pCalcInfo->ppResult && pCalcInfo->ppResult[0]) {
                pCalcInfo->ppResult[0][i] = pCalcInfo->pData[i].close;
            }
        }
        
        log_debug("Function executed successfully");
        return TRUE;
    }
};

// ============================================================================
// C-style Export Functions
// ============================================================================

BOOL RegisterKTFunc(KTFuncInfo** pInfo)
{
    if (pInfo == NULL)
    {
        return FALSE;
    }

    if (*pInfo == NULL)
    {
        // Initialize the plugin system if not already done
        if (!KTPluginManager::IsInitialized())
        {
            if (!KTPluginManager::Initialize())
            {
                log_error("Failed to initialize KT plugin system");
                return FALSE;
            }
        }
        
        // Get the dynamic function array from the registry
        auto& registry = KTFunctionRegistry::GetInstance();
        *pInfo = registry.GetCFunctionInfoArray();
        
        if (*pInfo == NULL)
        {
            log_error("Failed to get function array from registry");
            return FALSE;
        }
        
        // Validate memory layout compatibility with KT expectations
        if (!registry.ValidateMemoryLayout())
        {
            log_error("Function array memory layout validation failed");
            return FALSE;
        }
        
        size_t functionCount = registry.GetFunctionCount();
        log_debug(("KT Plugin registered " + std::to_string(functionCount) + " functions successfully (dynamic registry)").c_str());
        log_debug("Memory layout validation passed - array is KT-compatible");
        return TRUE;
    }

    return FALSE;
}

int GetFunctionCount()
{
    if (!KTPluginManager::IsInitialized())
    {
        return 0;
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    return static_cast<int>(registry.GetFunctionCount());
}

BOOL GetFunctionInfo(int nIndex, KTFuncInfo* pFuncInfo)
{
    if (pFuncInfo == NULL || nIndex < 0)
    {
        return FALSE;
    }
    
    if (!KTPluginManager::IsInitialized())
    {
        return FALSE;
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto functions = registry.GetAllFunctions();
    
    if (nIndex >= static_cast<int>(functions.size()))
    {
        return FALSE;
    }
    
    auto function = functions[nIndex];
    if (!function)
    {
        return FALSE;
    }
    
    pFuncInfo->nFuncMark = function->GetFunctionMark();
    pFuncInfo->pCallFunc = function->GetKTFunctionPointer();
    
    return TRUE;
}

BOOL CallFunction(int nIndex, CALCINFO* pCalcInfo)
{
    if (pCalcInfo == NULL || nIndex < 0)
    {
        return FALSE;
    }
    
    if (!KTPluginManager::IsInitialized())
    {
        return FALSE;
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto functions = registry.GetAllFunctions();
    
    if (nIndex >= static_cast<int>(functions.size()))
    {
        return FALSE;
    }
    
    auto function = functions[nIndex];
    if (!function)
    {
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr)
    {
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

// ============================================================================
// Direct Function Exports - Thin Wrapper Functions
// ============================================================================
// These functions provide direct exports that KT can call by name
// They internally dispatch to our framework functions

extern "C" {

/**
 * @brief Simple Moving Average - Direct Export Wrapper
 */
BOOL KT_SMA(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(static_cast<unsigned short>(KT_COMMON_FUNCTION_ID_OFFSET + 1)); // KT_SMA ID
    
    if (!function) {
        log_error("KT_SMA: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_SMA: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief Exponential Moving Average - Direct Export Wrapper
 */
BOOL KT_EMA(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(static_cast<unsigned short>(KT_COMMON_FUNCTION_ID_OFFSET + 2)); // KT_EMA ID
    
    if (!function) {
        log_error("KT_EMA: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_EMA: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief MACD Indicator - Direct Export Wrapper
 */
BOOL KT_MACD(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(static_cast<unsigned short>(KT_COMMON_FUNCTION_ID_OFFSET + 3)); // KT_MACD ID
    
    if (!function) {
        log_error("KT_MACD: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_MACD: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief RSI Indicator - Direct Export Wrapper
 */
BOOL KT_RSI(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(static_cast<unsigned short>(KT_COMMON_FUNCTION_ID_OFFSET + 4)); // KT_RSI ID
    
    if (!function) {
        log_error("KT_RSI: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_RSI: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

// Server functions (if enabled)
#if ENABLE_SERVER_FUNCTIONS

/**
 * @brief Server SMA - Direct Export Wrapper
 */
BOOL KT_SMA_SERVER(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(KT_SERVER_FUNCTION_ID_OFFSET + 10); // Server SMA ID
    
    if (!function) {
        log_error("KT_SMA_SERVER: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_SMA_SERVER: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief Server EMA - Direct Export Wrapper
 */
BOOL KT_EMA_SERVER(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(KT_SERVER_FUNCTION_ID_OFFSET + 11); // Server EMA ID
    
    if (!function) {
        log_error("KT_EMA_SERVER: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_EMA_SERVER: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief Server RSI - Direct Export Wrapper
 */
BOOL KT_RSI_SERVER(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(KT_SERVER_FUNCTION_ID_OFFSET + 12); // Server RSI ID
    
    if (!function) {
        log_error("KT_RSI_SERVER: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_RSI_SERVER: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief Server MACD - Direct Export Wrapper
 */
BOOL KT_MACD_SERVER(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(KT_SERVER_FUNCTION_ID_OFFSET + 13); // Server MACD ID
    
    if (!function) {
        log_error("KT_MACD_SERVER: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_MACD_SERVER: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

// =============================================================================
// Server Management Functions - Direct Export Wrappers
// =============================================================================

/**
 * @brief Server Connect - Direct Export Wrapper
 */
BOOL KT_SERVER_CONNECT(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(KT_SERVER_FUNCTION_ID_OFFSET + 2); // KTServer_Connect ID
    
    if (!function) {
        log_error("KT_SERVER_CONNECT: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_SERVER_CONNECT: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief Server Disconnect - Direct Export Wrapper
 */
BOOL KT_SERVER_DISCONNECT(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(KT_SERVER_FUNCTION_ID_OFFSET + 3); // KTServer_Disconnect ID
    
    if (!function) {
        log_error("KT_SERVER_DISCONNECT: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_SERVER_DISCONNECT: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief Server Status - Direct Export Wrapper
 */
BOOL KT_SERVER_STATUS(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(KT_SERVER_FUNCTION_ID_OFFSET + 4); // KTServer_GetStats ID
    
    if (!function) {
        log_error("KT_SERVER_STATUS: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_SERVER_STATUS: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief Server Send K-Bar - Direct Export Wrapper
 */
BOOL KT_SERVER_SEND_KBAR(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(KT_SERVER_FUNCTION_ID_OFFSET + 5); // KTServer_SendKBar ID
    
    if (!function) {
        log_error("KT_SERVER_SEND_KBAR: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_SERVER_SEND_KBAR: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

/**
 * @brief Server Call API - Direct Export Wrapper
 */
BOOL KT_SERVER_CALL_API(CALCINFO* pCalcInfo)
{
    if (!KTPluginManager::IsInitialized()) {
        KTPluginManager::Initialize();
    }
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(KT_SERVER_FUNCTION_ID_OFFSET + 6); // KTServer_CalculateSMA ID
    
    if (!function) {
        log_error("KT_SERVER_CALL_API: Function not found in registry");
        return FALSE;
    }
    
    pKTFUNC funcPtr = function->GetKTFunctionPointer();
    if (!funcPtr) {
        log_error("KT_SERVER_CALL_API: Invalid function pointer");
        return FALSE;
    }
    
    return funcPtr(pCalcInfo);
}

#endif // ENABLE_SERVER_FUNCTIONS

} // extern "C"

// ============================================================================
// KTPluginManager Implementation
// ============================================================================

/**
 * @brief Initialize the plugin system
 */
bool KTPluginManager::Initialize()
{
    if (s_initialized)
    {
        return true;
    }

    try
    {
        log_debug("Initializing KT Plugin System...");
        
        // Get registry instance and initialize
        auto& registry = KTFunctionRegistry::GetInstance();
        registry.InitializeDefaultFunctions();
        
        // Register built-in functions
        RegisterBuiltInFunctions();
        
        s_initialized = true;
        log_info("KT Plugin System initialized successfully");
        log_info(GetPluginInfo().c_str());
        
        return true;
    }
    catch (const std::exception& e)
    {
        log_error(("Failed to initialize KT Plugin System: " + std::string(e.what())).c_str());
        return false;
    }
    catch (...)
    {
        log_error("Failed to initialize KT Plugin System: Unknown error");
        return false;
    }
}

/**
 * @brief Cleanup the plugin system
 */
void KTPluginManager::Cleanup()
{
    if (!s_initialized)
    {
        return;
    }

    try
    {
        log_debug("Cleaning up KT Plugin System...");
        
        // Clear the registry
        auto& registry = KTFunctionRegistry::GetInstance();
        registry.Clear();
        
        s_initialized = false;
        log_info("KT Plugin System cleaned up successfully");
    }
    catch (const std::exception& e)
    {
        log_error(("Error during KT Plugin cleanup: " + std::string(e.what())).c_str());
    }
    catch (...)
    {
        log_error("Unknown error during KT Plugin cleanup");
    }
}

/**
 * @brief Get plugin information string
 */
std::string KTPluginManager::GetPluginInfo()
{
    std::ostringstream oss;
    oss << "=== KT Plugin Information ===\n";
    oss << "Plugin Name: QAUtils KT Plugin\n";
    oss << "Version: 1.0.0\n";
    oss << "Author: QAUtils Development Team\n";
    oss << "Description: Object-Oriented KT Plugin Framework\n";
    oss << "Initialized: " << (s_initialized ? "Yes" : "No") << "\n";
    
    if (s_initialized)
    {
        auto& registry = KTFunctionRegistry::GetInstance();
        oss << "\n" << registry.GetRegistryInfo();
    }
    
    return oss.str();
}

/**
 * @brief Register all built-in functions
 */
void KTPluginManager::RegisterBuiltInFunctions()
{
    auto& registry = KTFunctionRegistry::GetInstance();
    
    try
    {
        log_debug("Registering built-in functions...");
        
        // Register example functions
        bool success = true;

        success &= registry.RegisterFunction(std::make_shared<KTStubFunction>());
        
        // Register KT Common Functions (Technical Indicators)
        if (!RegisterKTCommonFunctions()) {
            log_error("Failed to register KT common functions");
            success = false;
        }
        
        // Register KT Server Functions (only if enabled)
#if ENABLE_SERVER_FUNCTIONS
        if (!RegisterKTServerFunctions()) {
            log_error("Failed to register KT server functions");
            success = false;
        }
#else
        log_info("Server functions disabled at compile time");
#endif
        
        // TODO: Register more functions here
        // success &= RegisterKTChanFunctions();
        
        if (success)
        {
            log_info("All built-in functions registered successfully");
        }
        else
        {
            log_warn("Some built-in functions failed to register");
        }
    }
    catch (const std::exception& e)
    {
        log_error(("Error registering built-in functions: " + std::string(e.what())).c_str());
    }
}

/**
 * @brief Check if plugin system is initialized
 */
bool KTPluginManager::IsInitialized()
{
    return s_initialized;
}

// ============================================================================
// DLL Entry Point
// ============================================================================

BOOL APIENTRY DllMain(HMODULE hinstDLL, DWORD fdwReason, LPVOID lpvReserved)
{
    switch (fdwReason)
    {
    case DLL_PROCESS_ATTACH:
        // Initialize logging
        log_init();
        log_set_level(LOG_DEBUG);
        // DLL is being loaded
        log_debug("KT Plugin DLL loaded");
        break;
        
    case DLL_PROCESS_DETACH:
        // DLL is being unloaded        
        log_debug("KT Plugin DLL unloading");
        KTPluginManager::Cleanup();
        log_close();
        break;
        
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
        // Thread-specific initialization/cleanup
        break;
    }
    
    return TRUE;
}