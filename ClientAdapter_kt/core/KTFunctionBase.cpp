#include "KTFunctionBase.h"
#include "KTFunctionRegistry.h"
#include "../utils/log.h"
#include <iostream>
#include <cstring>
#include <algorithm>

// Global debug mode flag (disabled by default)
bool KTFunctionBase::s_debugMode = false;

/**
 * @brief Constructor for KTFunctionBase
 * @param functionMark Unique function identifier
 * @param functionName Human-readable function name  
 * @param description Function description
 * @param category Function category
 * @param minInputCount Minimum required input count
 * @param supportsVariableParams Whether function handles variable parameters
 * @param expectedParamCount Expected parameter count
 * @param requiresFinancialData Whether function needs financial data
 * @param requiresExtendedData Whether function needs extended data
 */
KTFunctionBase::KTFunctionBase(unsigned short functionMark,
                              const std::string& functionName,
                              const std::string& description,
                              const std::string& category,
                              int minInputCount,
                              bool supportsVariableParams,
                              int expectedParamCount,
                              bool requiresFinancialData,
                              bool requiresExtendedData)
    : m_functionMark(functionMark)
    , m_functionName(functionName)
    , m_description(description)
    , m_category(category)
    , m_minInputCount(minInputCount)
    , m_supportsVariableParams(supportsVariableParams)
    , m_expectedParamCount(expectedParamCount)
    , m_requiresFinancialData(requiresFinancialData)
    , m_requiresExtendedData(requiresExtendedData)
{
}

/**
 * @brief Get the function mark/identifier
 * @return Function mark used by KT
 */
unsigned short KTFunctionBase::GetFunctionMark() const
{
    return m_functionMark;
}

/**
 * @brief Get the function name
 * @return Human-readable function name
 */
std::string KTFunctionBase::GetFunctionName() const
{
    return m_functionName;
}

/**
 * @brief Get the function description
 * @return Function description
 */
std::string KTFunctionBase::GetDescription() const
{
    return m_description;
}

/**
 * @brief Get the function category
 * @return Function category
 */
std::string KTFunctionBase::GetCategory() const
{
    return m_category;
}

/**
 * @brief Get minimum input count
 * @return Minimum required input count
 */
int KTFunctionBase::GetMinInputCount() const
{
    return m_minInputCount;
}

/**
 * @brief Check if function supports variable parameters
 * @return true if function handles variable parameters
 */
bool KTFunctionBase::SupportsVariableInputs() const
{
    return m_supportsVariableParams;
}

/**
 * @brief Get expected parameter count
 * @return Expected number of parameters
 */
int KTFunctionBase::GetExpectedParameterCount() const
{
    return m_expectedParamCount;
}

/**
 * @brief Check if function requires financial data
 * @return true if function needs financial data
 */
bool KTFunctionBase::RequiresFinancialData() const
{
    return m_requiresFinancialData;
}

/**
 * @brief Check if function requires extended data
 * @return true if function needs extended data
 */
bool KTFunctionBase::RequiresExtendedData() const
{
    return m_requiresExtendedData;
}

/**
 * @brief Get parameter names
 * @return Vector of parameter names
 */
std::vector<std::string> KTFunctionBase::GetParameterNames() const
{
    // Default implementation - derived classes should override
    std::vector<std::string> names;
    for (int i = 0; i < m_expectedParamCount; ++i) {
        names.push_back("Param" + std::to_string(i + 1));
    }
    return names;
}

/**
 * @brief Get parameter descriptions
 * @return Vector of parameter descriptions
 */
std::vector<std::string> KTFunctionBase::GetParameterDescriptions() const
{
    // Default implementation - derived classes should override
    std::vector<std::string> descriptions;
    for (int i = 0; i < m_expectedParamCount; ++i) {
        descriptions.push_back("Parameter " + std::to_string(i + 1) + " for " + m_functionName);
    }
    return descriptions;
}

/**
 * @brief Validate if function is properly configured
 * @return true if function is ready for registration
 */
bool KTFunctionBase::IsValid() const
{
    return m_functionMark > 0 && !m_functionName.empty();
}

/**
 * @brief Validate CALCINFO structure
 * @param pData Pointer to CALCINFO structure
 * @return true if CALCINFO is valid
 */
bool KTFunctionBase::ValidateCALCINFO(const CALCINFO* pData) const
{
    return ValidateCALCINFOStatic(pData, m_functionName);
}

/**
 * @brief Static utility: Basic CALCINFO validation
 * @param pData Pointer to CALCINFO structure
 * @param functionName Function name for error logging
 * @return true if CALCINFO is valid
 */
bool KTFunctionBase::ValidateCALCINFOStatic(const CALCINFO* pData, const std::string& functionName)
{
    if (!pData) {
        LogError(functionName, "CALCINFO pointer is null");
        return false;
    }

    if (pData->nCount == 0) {
        LogError(functionName, "No data available (nCount = 0)");
        return false;
    }
    
    if (!pData->pData) {
        LogError(functionName, "Data pointer is null");
        return false;
    }
    
    if (!pData->ppResult) {
        LogError(functionName, "Result buffer is null");
        return false;
    }

    return true;
}

/**
 * @brief Extract close prices from CALCINFO
 * @param pData Pointer to CALCINFO structure
 * @return Vector of close prices
 */
std::vector<float> KTFunctionBase::ExtractClosePrice(const CALCINFO* pData)
{
    std::vector<float> prices;
    if (!pData || !pData->pData) {
        return prices;
    }

    prices.reserve(pData->nCount);
    for (int i = 0; i < pData->nCount; ++i) {
        prices.push_back(pData->pData[i].close);
    }
    return prices;
}

/**
 * @brief Extract open prices from CALCINFO
 * @param pData Pointer to CALCINFO structure
 * @return Vector of open prices
 */
std::vector<float> KTFunctionBase::ExtractOpenPrice(const CALCINFO* pData)
{
    std::vector<float> prices;
    if (!pData || !pData->pData) {
        return prices;
    }

    prices.reserve(pData->nCount);
    for (int i = 0; i < pData->nCount; ++i) {
        prices.push_back(pData->pData[i].open);
    }
    return prices;
}

/**
 * @brief Extract high prices from CALCINFO
 * @param pData Pointer to CALCINFO structure
 * @return Vector of high prices
 */
std::vector<float> KTFunctionBase::ExtractHighPrice(const CALCINFO* pData)
{
    std::vector<float> prices;
    if (!pData || !pData->pData) {
        return prices;
    }

    prices.reserve(pData->nCount);
    for (int i = 0; i < pData->nCount; ++i) {
        prices.push_back(pData->pData[i].high);
    }
    return prices;
}

/**
 * @brief Extract low prices from CALCINFO
 * @param pData Pointer to CALCINFO structure
 * @return Vector of low prices
 */
std::vector<float> KTFunctionBase::ExtractLowPrice(const CALCINFO* pData)
{
    std::vector<float> prices;
    if (!pData || !pData->pData) {
        return prices;
    }

    prices.reserve(pData->nCount);
    for (int i = 0; i < pData->nCount; ++i) {
        prices.push_back(pData->pData[i].low);
    }
    return prices;
}

/**
 * @brief Extract volume data from CALCINFO
 * @param pData Pointer to CALCINFO structure
 * @return Vector of volume data
 */
std::vector<float> KTFunctionBase::ExtractVolume(const CALCINFO* pData)
{
    std::vector<float> volumes;
    if (!pData || !pData->pData) {
        return volumes;
    }

    volumes.reserve(pData->nCount);
    for (int i = 0; i < pData->nCount; ++i) {
        volumes.push_back(pData->pData[i].volume);
    }
    return volumes;
}

/**
 * @brief Extract amount data from CALCINFO
 * @param pData Pointer to CALCINFO structure
 * @return Vector of amount data
 */
std::vector<float> KTFunctionBase::ExtractAmount(const CALCINFO* pData)
{
    std::vector<float> amounts;
    if (!pData || !pData->pData) {
        return amounts;
    }

    amounts.reserve(pData->nCount);
    for (int i = 0; i < pData->nCount; ++i) {
        amounts.push_back(pData->pData[i].amount);
    }
    return amounts;
}

/**
 * @brief Get K-bar data at specific index
 * @param pData Pointer to CALCINFO structure
 * @param index Index of the K-bar (0-based)
 * @return Pointer to STKDATA or nullptr if invalid
 */
const STKDATA* KTFunctionBase::GetKbarData(const CALCINFO* pData, int index)
{
    if (!pData || !pData->pData || index < 0 || index >= pData->nCount) {
        return nullptr;
    }
    return &pData->pData[index];
}

/**
 * @brief Get parameter value by index
 * @param pData Pointer to CALCINFO structure
 * @param paramIndex Parameter index (0-based)
 * @param defaultValue Default value if parameter not available
 * @return Parameter value
 */
float KTFunctionBase::GetParameterValue(const CALCINFO* pData, int paramIndex, float defaultValue)
{
    if (!pData || !pData->pParam || paramIndex < 0 || paramIndex >= pData->pParam->nParamCount) {
        return defaultValue;
    }
    return pData->pParam->pParam[paramIndex];
}

/**
 * @brief Get constant parameter value
 * @param pData Pointer to CALCINFO structure
 * @param paramIndex Parameter index (0-based)
 * @param defaultValue Default value if parameter not available
 * @return Constant parameter value
 */
float KTFunctionBase::GetConstantParam(const CALCINFO* pData, int paramIndex, float defaultValue)
{
    return GetParameterValue(pData, paramIndex, defaultValue);
}

/**
 * @brief Get array parameter pointer
 * @param pData Pointer to CALCINFO structure
 * @param paramIndex Parameter index (0-based, 0=m_pfParam1, 1=m_pfParam2, etc.)
 * @return Pointer to parameter array or nullptr if not available
 */
const float* KTFunctionBase::GetArrayParam(const CALCINFO* pData, int paramIndex)
{
    if (!pData) {
        return nullptr;
    }

    // Note: This function may need to be redesigned based on actual KT parameter structure
    // For now, return nullptr as the parameter structure is different
    return nullptr;
}

/**
 * @brief Safe result writing with bounds checking
 * @param pData Pointer to CALCINFO structure
 * @param index Result index
 * @param value Value to write
 * @return true if write succeeded
 */
bool KTFunctionBase::WriteResult(CALCINFO* pData, int index, float value)
{
    if (!pData || !pData->ppResult || !pData->ppResult[0] || index < 0 || index >= pData->nCount) {
        return false;
    }
    pData->ppResult[0][index] = value;
    return true;
}

/**
 * @brief Initialize result buffer with default value
 * @param pData Pointer to CALCINFO structure
 * @param defaultValue Default value to use
 * @param startIndex Starting index
 */
void KTFunctionBase::InitializeResults(CALCINFO* pData, float defaultValue, int startIndex)
{
    if (!pData || !pData->ppResult || !pData->ppResult[0] || startIndex < 0) {
        return;
    }

    for (int i = startIndex; i < pData->nCount; ++i) {
        pData->ppResult[0][i] = defaultValue;
    }
}

/**
 * @brief Check if financial data is available
 * @param pData Pointer to CALCINFO structure
 * @return true if financial data is available
 */
bool KTFunctionBase::HasFinancialData(const CALCINFO* pData)
{
    return pData && pData->pSplitData && pData->nSplitDataCount > 0;
}

/**
 * @brief Check if extended data is available
 * @param pData Pointer to CALCINFO structure
 * @return true if extended data is available
 */
bool KTFunctionBase::HasExtendedData(const CALCINFO* pData)
{
    return pData && pData->pDataEx;
}

/**
 * @brief Log error message
 * @param functionName Name of the function reporting the error
 * @param message Error message
 */
void KTFunctionBase::LogError(const std::string& functionName, const std::string& message)
{
    std::string fullMessage = "[" + functionName + "] ERROR: " + message;
    Log::Error(fullMessage);
    if (s_debugMode) {
        std::cerr << fullMessage << std::endl;
    }
}

/**
 * @brief Log debug message
 * @param functionName Name of the function reporting the debug info
 * @param message Debug message
 */
void KTFunctionBase::LogDebug(const std::string& functionName, const std::string& message)
{
    if (s_debugMode) {
        std::string fullMessage = "[" + functionName + "] DEBUG: " + message;
        Log::Debug(fullMessage);
        std::cout << fullMessage << std::endl;
    }
}

/**
 * @brief Log function call information
 * @param functionName Name of the function being called
 * @param pData Pointer to CALCINFO structure
 */
void KTFunctionBase::LogFunctionCall(const std::string& functionName, const CALCINFO* pData)
{
    if (s_debugMode && pData) {
        std::ostringstream oss;
        oss << "Function call: " << functionName
            << ", DataNum: " << pData->nCount
            << ", DataType: " << static_cast<int>(pData->nType)
            << ", Stock: " << pData->szLabel;
        LogDebug(functionName, oss.str());
    }
}

/**
 * @brief Get function instance from registry
 * @param functionMark Function identifier
 * @return Function instance or nullptr if not found
 */
KTFunctionPtr KTFunctionBase::GetFunctionFromRegistry(unsigned short functionMark)
{
    // This will be implemented when KTFunctionRegistry is available
    // For now, return nullptr
    return nullptr;
}

/**
 * @brief Set global debug mode
 * @param enabled Whether to enable debug logging
 */
void KTFunctionBase::SetDebugMode(bool enabled)
{
    s_debugMode = enabled;
    if (enabled) {
        LogDebug("KTFunctionBase", "Debug mode enabled");
    }
}

/**
 * @brief Check if debug mode is enabled
 * @return true if debug mode is on
 */
bool KTFunctionBase::IsDebugMode()
{
    return s_debugMode;
}