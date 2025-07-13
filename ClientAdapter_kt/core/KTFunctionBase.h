#ifndef __KT_FUNCTION_BASE_H__
#define __KT_FUNCTION_BASE_H__

#include "IKTFunction.h"
#include <stdexcept>
#include <sstream>
#include <vector>

// KT Export macro definition
#define KT_EXPORT(funcname) extern "C" __declspec(dllexport) int WINAPI funcname(CALCINFO* pData)

// Forward declaration to avoid circular dependency
class KTFunctionRegistry;

/**
 * @brief Base implementation class for KT functions
 * 
 * This class provides common functionality and default implementations
 * for IKTFunction metadata methods. Derived classes must implement
 * their own C-style function and provide it through GetKTFunctionPointer().
 * 
 * The C-style function should contain all calculation logic and can use
 * the utility methods provided by this base class for logging and validation.
 */
class KTFunctionBase : public IKTFunction
{
protected:
    unsigned short m_functionMark;      /**< Function identifier */
    std::string m_functionName;         /**< Function name */
    std::string m_description;          /**< Function description */
    std::string m_category;             /**< Function category */
    int m_minInputCount;                /**< Minimum required input count */
    bool m_supportsVariableParams;      /**< Whether function handles variable parameters */
    int m_expectedParamCount;           /**< Expected parameter count */
    bool m_requiresFinancialData;       /**< Whether function needs financial data */
    bool m_requiresExtendedData;        /**< Whether function needs extended data */
    
    static bool s_debugMode;            /**< Global debug mode flag */

public:
    /**
     * @brief Constructor
     * @param functionMark Unique function identifier for KT
     * @param functionName Human-readable function name
     * @param description Function description
     * @param category Function category (default: "Custom")
     * @param minInputCount Minimum required input count (default: 1)
     * @param supportsVariableParams Whether function handles variable parameters (default: false)
     * @param expectedParamCount Expected parameter count (default: 0)
     * @param requiresFinancialData Whether function needs financial data (default: false)
     * @param requiresExtendedData Whether function needs extended data (default: false)
     */
    KTFunctionBase(unsigned short functionMark, 
                   const std::string& functionName,
                   const std::string& description,
                   const std::string& category = "Custom",
                   int minInputCount = 1,
                   bool supportsVariableParams = false,
                   int expectedParamCount = 0,
                   bool requiresFinancialData = false,
                   bool requiresExtendedData = false);

    /**
     * @brief Destructor
     */
    virtual ~KTFunctionBase() = default;

    // IKTFunction interface implementation
    unsigned short GetFunctionMark() const override;
    std::string GetFunctionName() const override;
    std::string GetDescription() const override;
    std::string GetCategory() const override;
    int GetMinInputCount() const override;
    bool SupportsVariableInputs() const override;
    int GetExpectedParameterCount() const override;
    bool RequiresFinancialData() const override;
    bool RequiresExtendedData() const override;
    
    /**
     * @brief Get parameter names
     * @return Vector of parameter names
     */
    std::vector<std::string> GetParameterNames() const override;
    
    /**
     * @brief Get parameter descriptions
     * @return Vector of parameter descriptions
     */
    std::vector<std::string> GetParameterDescriptions() const override;

    /**
     * @brief Default validation - checks if function mark is valid
     * @return true if function is properly configured
     */
    bool IsValid() const override;

    /**
     * @brief Get C-style function pointer (must be overridden by derived classes)
     * 
     * Derived classes must provide their own static C-style function that
     * implements the actual calculation logic. This function will be called
     * directly by KT.
     * 
     * @return Function pointer for KT registration
     */
    pKTFUNC GetKTFunctionPointer() const override = 0;

    /**
     * @brief Utility: Basic CALCINFO validation for C-style functions
     * @param pData Pointer to CALCINFO structure
     * @return true if CALCINFO is valid
     */
    bool ValidateCALCINFO(const CALCINFO* pData) const;

    /**
     * @brief Static utility: Basic CALCINFO validation for C-style functions
     * @param pData Pointer to CALCINFO structure
     * @param functionName Function name for error logging
     * @return true if CALCINFO is valid
     */
    static bool ValidateCALCINFOStatic(const CALCINFO* pData, const std::string& functionName);

public:
    /**
     * @brief Utility: Extract close prices from CALCINFO
     * @param pData Pointer to CALCINFO structure
     * @return Vector of close prices
     */
    static std::vector<float> ExtractClosePrice(const CALCINFO* pData);

    /**
     * @brief Utility: Extract open prices from CALCINFO
     * @param pData Pointer to CALCINFO structure
     * @return Vector of open prices
     */
    static std::vector<float> ExtractOpenPrice(const CALCINFO* pData);

    /**
     * @brief Utility: Extract high prices from CALCINFO
     * @param pData Pointer to CALCINFO structure
     * @return Vector of high prices
     */
    static std::vector<float> ExtractHighPrice(const CALCINFO* pData);

    /**
     * @brief Utility: Extract low prices from CALCINFO
     * @param pData Pointer to CALCINFO structure
     * @return Vector of low prices
     */
    static std::vector<float> ExtractLowPrice(const CALCINFO* pData);

    /**
     * @brief Utility: Extract volume data from CALCINFO
     * @param pData Pointer to CALCINFO structure
     * @return Vector of volume data
     */
    static std::vector<float> ExtractVolume(const CALCINFO* pData);

    /**
     * @brief Utility: Extract amount data from CALCINFO
     * @param pData Pointer to CALCINFO structure
     * @return Vector of amount data
     */
    static std::vector<float> ExtractAmount(const CALCINFO* pData);

    /**
     * @brief Utility: Get K-bar data at specific index
     * @param pData Pointer to CALCINFO structure
     * @param index Index of the K-bar (0-based)
     * @return Pointer to STKDATA or nullptr if invalid
     */
    static const STKDATA* GetKbarData(const CALCINFO* pData, int index);

    /**
     * @brief Utility: Get parameter value by index
     * @param pData Pointer to CALCINFO structure
     * @param paramIndex Parameter index (0-based)
     * @param defaultValue Default value if parameter not available
     * @return Parameter value
     */
    static float GetParameterValue(const CALCINFO* pData, int paramIndex, float defaultValue = 0.0f);

    /**
     * @brief Utility: Get constant parameter value
     * @param pData Pointer to CALCINFO structure
     * @param paramIndex Parameter index (0-based)
     * @param defaultValue Default value if parameter not available
     * @return Constant parameter value
     */
    static float GetConstantParam(const CALCINFO* pData, int paramIndex, float defaultValue = 0.0f);

    /**
     * @brief Utility: Get array parameter pointer
     * @param pData Pointer to CALCINFO structure
     * @param paramIndex Parameter index (0-based, 0=m_pfParam1, 1=m_pfParam2, etc.)
     * @return Pointer to parameter array or nullptr if not available
     */
    static const float* GetArrayParam(const CALCINFO* pData, int paramIndex);

    /**
     * @brief Utility: Safe result writing with bounds checking
     * @param pData Pointer to CALCINFO structure
     * @param index Result index
     * @param value Value to write
     * @return true if write succeeded
     */
    static bool WriteResult(CALCINFO* pData, int index, float value);

    /**
     * @brief Utility: Initialize result buffer with default value
     * @param pData Pointer to CALCINFO structure
     * @param defaultValue Default value to use (default: 0.0f)
     * @param startIndex Starting index (default: 0)
     */
    static void InitializeResults(CALCINFO* pData, float defaultValue = 0.0f, int startIndex = 0);

    /**
     * @brief Utility: Check if financial data is available
     * @param pData Pointer to CALCINFO structure
     * @return true if financial data is available
     */
    static bool HasFinancialData(const CALCINFO* pData);

    /**
     * @brief Utility: Check if extended data is available
     * @param pData Pointer to CALCINFO structure
     * @return true if extended data is available
     */
    static bool HasExtendedData(const CALCINFO* pData);

    /**
     * @brief Log error message (can be overridden for custom logging)
     * @param functionName Name of the function reporting the error
     * @param message Error message
     */
    static void LogError(const std::string& functionName, const std::string& message);

    /**
     * @brief Log debug message (can be overridden for custom logging)
     * @param functionName Name of the function reporting the debug info
     * @param message Debug message
     */
    static void LogDebug(const std::string& functionName, const std::string& message);

    /**
     * @brief Log function call information
     * @param functionName Name of the function being called
     * @param pData Pointer to CALCINFO structure
     */
    static void LogFunctionCall(const std::string& functionName, const CALCINFO* pData);

    /**
     * @brief Get function instance from registry for logging/utilities
     * @param functionMark Function identifier
     * @return Function instance or nullptr if not found
     */
    static KTFunctionPtr GetFunctionFromRegistry(unsigned short functionMark);

public:
    /**
     * @brief Set global debug mode
     * @param enabled Whether to enable debug logging
     */
    static void SetDebugMode(bool enabled);

    /**
     * @brief Check if debug mode is enabled
     * @return true if debug mode is on
     */
    static bool IsDebugMode();
};

#endif // __KT_FUNCTION_BASE_H__