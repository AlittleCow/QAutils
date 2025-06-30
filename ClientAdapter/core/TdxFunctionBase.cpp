#include "TdxFunctionBase.h"
#include <iostream>
#include <cstring>

// Thread-local storage for current instance
thread_local TdxFunctionBase* TdxFunctionBase::s_currentInstance = nullptr;

// Global debug mode flag (disabled by default)
bool TdxFunctionBase::s_debugMode = false;

/**
 * @brief Constructor for TdxFunctionBase
 * @param functionMark Unique function identifier
 * @param functionName Human-readable function name  
 * @param description Function description
 */
TdxFunctionBase::TdxFunctionBase(unsigned short functionMark,
                                const std::string& functionName,
                                const std::string& description)
    : m_functionMark(functionMark)
    , m_functionName(functionName)
    , m_description(description)
{
}

/**
 * @brief Get the function mark/identifier
 * @return Function mark used by TDX
 */
unsigned short TdxFunctionBase::GetFunctionMark() const
{
    return m_functionMark;
}

/**
 * @brief Get the function name
 * @return Human-readable function name
 */
std::string TdxFunctionBase::GetFunctionName() const
{
    return m_functionName;
}

/**
 * @brief Get the function description
 * @return Description of what the function does
 */
std::string TdxFunctionBase::GetDescription() const
{
    return m_description;
}

/**
 * @brief Validate input parameters
 * @param nCount Number of data points
 * @param pOut Output array pointer
 * @param pInA Input array A pointer
 * @param pInB Input array B pointer
 * @param pInC Input array C pointer
 * @return true if inputs are valid
 */
bool TdxFunctionBase::ValidateInputs(int nCount, const float* pOut, const float* pInA,
                                    const float* pInB, const float* pInC) const
{
    // Suppress unused parameter warnings for base implementation
    (void)pInA;
    (void)pInB;
    (void)pInC;
    
    if (nCount <= 0)
    {
        LogError("Invalid data count: " + std::to_string(nCount));
        return false;
    }

    if (pOut == nullptr)
    {
        LogError("Output array is null");
        return false;
    }

    // Note: Input arrays can be null depending on function requirements
    // Derived classes should override this method for specific validation
    
    return true;
}

/**
 * @brief Execute the function with error handling
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Input array A
 * @param pInB Input array B
 * @param pInC Input array C
 * @return true if execution succeeded
 */
bool TdxFunctionBase::Execute(int nCount, float* pOut, const float* pInA,
                             const float* pInB, const float* pInC)
{
    try
    {
        if (!ValidateInputs(nCount, pOut, pInA, pInB, pInC))
        {
            return false;
        }

        LogDebug("Executing function: " + m_functionName + " with " + std::to_string(nCount) + " data points");
        
        return CalculateCore(nCount, pOut, pInA, pInB, pInC);
    }
    catch (const std::exception& e)
    {
        LogError("Exception in " + m_functionName + ": " + e.what());
        return false;
    }
    catch (...)
    {
        LogError("Unknown exception in " + m_functionName);
        return false;
    }
}

/**
 * @brief Get C-style function pointer for TDX registration
 * @return Function pointer compatible with TDX interface
 */
pPluginFUNC TdxFunctionBase::GetCFunctionPointer()
{
    return &TdxFunctionBase::CStyleWrapper;
}

/**
 * @brief Set current instance for C wrapper access
 */
void TdxFunctionBase::SetCurrentInstance()
{
    s_currentInstance = this;
}

/**
 * @brief C-style wrapper function for TDX compatibility
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Input array A
 * @param pInB Input array B
 * @param pInC Input array C
 */
void TdxFunctionBase::CStyleWrapper(int nCount, float* pOut, float* pInA, float* pInB, float* pInC)
{
    if (s_currentInstance == nullptr)
    {
        // Fill output with zeros if no instance is set
        if (pOut != nullptr && nCount > 0)
        {
            std::memset(pOut, 0, nCount * sizeof(float));
        }
        return;
    }

    // Execute the function through the current instance
    s_currentInstance->Execute(nCount, pOut, pInA, pInB, pInC);
}

/**
 * @brief Log error message to debug output
 * @param message Error message to log
 */
void TdxFunctionBase::LogError(const std::string& message) const
{
    std::string logMsg = "[ERROR] " + m_functionName + ": " + message;
    std::cerr << logMsg << std::endl;
    
    // Output to Windows debug console if available
    #ifdef _WIN32
    OutputDebugStringA((logMsg + "\n").c_str());
    #endif
}

/**
 * @brief Log debug message
 * @param message Debug message to log
 */
void TdxFunctionBase::LogDebug(const std::string& message) const
{
    if (s_debugMode)  // Use runtime debug flag instead of compile-time macro
    {
        std::string logMsg = "[DEBUG] " + m_functionName + ": " + message;
        std::cout << logMsg << std::endl;
        
        // Output to Windows debug console if available
        #ifdef _WIN32
        OutputDebugStringA((logMsg + "\n").c_str());
        #endif
    }
}

/**
 * @brief Enable or disable debug mode globally
 * @param enable true to enable debug logging, false to disable
 */
void TdxFunctionBase::SetDebugMode(bool enable)
{
    s_debugMode = enable;
    if (enable)
    {
        std::cout << "[DEBUG] Debug mode enabled for all TDX functions" << std::endl;
    }
    else
    {
        std::cout << "[INFO] Debug mode disabled for all TDX functions" << std::endl;
    }
}

/**
 * @brief Check if debug mode is enabled
 * @return true if debug mode is enabled
 */
bool TdxFunctionBase::IsDebugMode()
{
    return s_debugMode;
} 