#include "TdxFunctionBase.h"
#include "TdxFunctionRegistry.h"
#include "../utils/log.h"
#include <iostream>
#include <cstring>
#include <algorithm>

// Global debug mode flag (disabled by default)
bool TdxFunctionBase::s_debugMode = false;

/**
 * @brief Constructor for TdxFunctionBase
 * @param functionMark Unique function identifier
 * @param functionName Human-readable function name  
 * @param description Function description
 * @param category Function category
 * @param minInputCount Minimum required input count
 * @param supportsVariableInputs Whether function handles nullptr inputs
 */
TdxFunctionBase::TdxFunctionBase(unsigned short functionMark,
                                const std::string& functionName,
                                const std::string& description,
                                const std::string& category,
                                int minInputCount,
                                bool supportsVariableInputs)
    : m_functionMark(functionMark)
    , m_functionName(functionName)
    , m_description(description)
    , m_category(category)
    , m_minInputCount(minInputCount)
    , m_supportsVariableInputs(supportsVariableInputs)
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
 * @brief Get the function category
 * @return Function category string
 */
std::string TdxFunctionBase::GetCategory() const
{
    return m_category;
}

/**
 * @brief Get minimum required input count
 * @return Minimum number of data points needed
 */
int TdxFunctionBase::GetMinInputCount() const
{
    return m_minInputCount;
}

/**
 * @brief Check if function supports variable input arrays
 * @return true if function can handle nullptr input arrays
 */
bool TdxFunctionBase::SupportsVariableInputs() const
{
    return m_supportsVariableInputs;
}

/**
 * @brief Get parameter information
 * @return Default parameter description
 */
std::string TdxFunctionBase::GetParameterInfo() const
{
    return "nCount=data points, pOut=output array, pInA/B/C=input arrays";
}

/**
 * @brief Validate if function is properly configured
 * @return true if function mark is valid and configuration is complete
 */
bool TdxFunctionBase::IsValid() const
{
    return m_functionMark > 0 && !m_functionName.empty() && !m_description.empty();
}

/**
 * @brief Basic input validation for C-style functions
 * @param nCount Number of data points
 * @param pOut Output array pointer
 * @param pInA Input array A pointer
 * @param pInB Input array B pointer
 * @param pInC Input array C pointer
 * @return true if inputs are valid
 */
bool TdxFunctionBase::ValidateBasicInputs(int nCount, const float* pOut, const float* pInA,
                                         const float* pInB, const float* pInC) const
{
    // Check data count
    if (nCount <= 0)
    {
        LogError(m_functionName, "Invalid data count: " + std::to_string(nCount));
        return false;
    }

    if (nCount < m_minInputCount)
    {
        LogError(m_functionName, "Data count " + std::to_string(nCount) + 
                " is less than minimum required " + std::to_string(m_minInputCount));
        return false;
    }

    // Check output array
    if (pOut == nullptr)
    {
        LogError(m_functionName, "Output array is null");
        return false;
    }

    // Check required inputs (function-specific)
    if (!m_supportsVariableInputs)
    {
        if (pInA == nullptr)
        {
            LogError(m_functionName, "Input array A is required but null");
            return false;
        }
    }

    return true;
}

/**
 * @brief Safe array copy with bounds checking
 * @param dest Destination array
 * @param src Source array
 * @param count Number of elements to copy
 * @return true if copy succeeded
 */
bool TdxFunctionBase::SafeArrayCopy(float* dest, const float* src, int count)
{
    if (dest == nullptr || src == nullptr || count <= 0)
    {
        return false;
    }

    try
    {
        // Use std::copy for better performance and safety
        std::copy(src, src + count, dest);
        return true;
    }
    catch (...)
    {
        return false;
    }
}

/**
 * @brief Initialize output array with default value
 * @param pOut Output array
 * @param count Number of elements
 * @param defaultValue Default value to use
 */
void TdxFunctionBase::InitializeOutput(float* pOut, int count, float defaultValue)
{
    if (pOut == nullptr || count <= 0)
    {
        return;
    }

    std::fill(pOut, pOut + count, defaultValue);
}

/**
 * @brief Check if array pointer is valid for given count
 * @param ptr Array pointer
 * @param count Expected element count
 * @return true if pointer appears to be valid
 */
bool TdxFunctionBase::IsValidArrayPointer(const float* ptr, int count)
{
    // Basic null check
    if (ptr == nullptr)
    {
        return false;
    }

    // Count should be positive
    if (count <= 0)
    {
        return false;
    }

    // Note: We can't do comprehensive validation without platform-specific code
    // This is a basic sanity check
    return true;
}

/**
 * @brief Log error message
 * @param functionName Name of the function reporting the error
 * @param message Error message
 */
void TdxFunctionBase::LogError(const std::string& functionName, const std::string& message)
{
    log_error("%s: %s", functionName.c_str(), message.c_str());
}

/**
 * @brief Log debug message
 * @param functionName Name of the function reporting the debug info
 * @param message Debug message
 */
void TdxFunctionBase::LogDebug(const std::string& functionName, const std::string& message)
{
    if (s_debugMode)
    {
        log_debug("%s: %s", functionName.c_str(), message.c_str());
    }
}

/**
 * @brief Log function call information
 * @param functionName Name of the function being called
 * @param nCount Number of data points
 * @param hasA Whether input A is provided
 * @param hasB Whether input B is provided
 * @param hasC Whether input C is provided
 */
void TdxFunctionBase::LogFunctionCall(const std::string& functionName, int nCount, 
                                     bool hasA, bool hasB, bool hasC)
{
    if (s_debugMode)
    {
        log_debug("%s called: count=%d, inputs=[A:%s, B:%s, C:%s]", 
                 functionName.c_str(), nCount,
                 hasA ? "Yes" : "No",
                 hasB ? "Yes" : "No", 
                 hasC ? "Yes" : "No");
    }
}

/**
 * @brief Get function instance from registry for logging/utilities
 * @param functionMark Function identifier
 * @return Function instance or nullptr if not found
 */
TdxFunctionPtr TdxFunctionBase::GetFunctionFromRegistry(unsigned short functionMark)
{
    try
    {
        auto& registry = TdxFunctionRegistry::GetInstance();
        return registry.GetFunction(functionMark);
    }
    catch (...)
    {
        // Registry might not be available during certain phases
        return nullptr;
    }
}

/**
 * @brief Set global debug mode
 * @param enabled Whether to enable debug logging
 */
void TdxFunctionBase::SetDebugMode(bool enabled)
{
    s_debugMode = enabled;
    if (enabled)
    {
        log_debug("TdxFunctionBase debug mode enabled");
    }
}

/**
 * @brief Check if debug mode is enabled
 * @return true if debug mode is on
 */
bool TdxFunctionBase::IsDebugMode()
{
    return s_debugMode;
}

/**
 * @brief Static utility: Basic input validation for C-style functions
 * @param nCount Number of data points
 * @param pOut Output array
 * @param functionName Function name for error logging
 * @return true if basic inputs are valid
 */
bool TdxFunctionBase::ValidateBasicInputsStatic(int nCount, const float* pOut, const std::string& functionName)
{
    // Check data count
    if (nCount <= 0)
    {
        LogError(functionName, "Invalid data count: " + std::to_string(nCount));
        return false;
    }

    // Check output array
    if (pOut == nullptr)
    {
        LogError(functionName, "Output array is null");
        return false;
    }

    return true;
}