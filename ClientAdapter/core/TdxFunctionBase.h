#ifndef __TDX_FUNCTION_BASE_H__
#define __TDX_FUNCTION_BASE_H__

#include "ITdxFunction.h"
#include <stdexcept>
#include <sstream>

// Forward declaration to avoid circular dependency
class TdxFunctionRegistry;

/**
 * @brief Base implementation class for TDX functions
 * 
 * This class provides common functionality and default implementations
 * for ITdxFunction metadata methods. Derived classes must implement
 * their own C-style function and provide it through GetCFunctionPointer().
 * 
 * The C-style function should contain all calculation logic and can use
 * the utility methods provided by this base class for logging and validation.
 */
class TdxFunctionBase : public ITdxFunction
{
protected:
    unsigned short m_functionMark;  /**< Function identifier */
    std::string m_functionName;     /**< Function name */
    std::string m_description;      /**< Function description */
    std::string m_category;         /**< Function category */
    int m_minInputCount;            /**< Minimum required input count */
    bool m_supportsVariableInputs;  /**< Whether function handles nullptr inputs */
    
    static bool s_debugMode;        /**< Global debug mode flag */

public:
    /**
     * @brief Constructor
     * @param functionMark Unique function identifier for TDX
     * @param functionName Human-readable function name
     * @param description Function description
     * @param category Function category (default: "Custom")
     * @param minInputCount Minimum required input count (default: 1)
     * @param supportsVariableInputs Whether function handles nullptr inputs (default: false)
     */
    TdxFunctionBase(unsigned short functionMark, 
                   const std::string& functionName,
                   const std::string& description,
                   const std::string& category = "Custom",
                   int minInputCount = 1,
                   bool supportsVariableInputs = false);

    /**
     * @brief Destructor
     */
    virtual ~TdxFunctionBase() = default;

    // ITdxFunction interface implementation
    unsigned short GetFunctionMark() const override;
    std::string GetFunctionName() const override;
    std::string GetDescription() const override;
    std::string GetCategory() const override;
    int GetMinInputCount() const override;
    bool SupportsVariableInputs() const override;
    
    /**
     * @brief Default parameter information
     * @return Parameter description string
     */
    std::string GetParameterInfo() const override;

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
     * directly by TDX.
     * 
     * @return Function pointer for TDX registration
     */
    pPluginFUNC GetCFunctionPointer() override = 0;

    /**
     * @brief Utility: Basic input validation for C-style functions
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Input array A (can be nullptr if function supports it)
     * @param pInB Input array B (can be nullptr if function supports it)
     * @param pInC Input array C (can be nullptr if function supports it)
     * @return true if inputs are valid
     */
    bool ValidateBasicInputs(int nCount, const float* pOut, const float* pInA,
                            const float* pInB, const float* pInC) const;

    /**
     * @brief Static utility: Basic input validation for C-style functions
     * @param nCount Number of data points
     * @param pOut Output array
     * @param functionName Function name for error logging
     * @return true if basic inputs are valid
     */
    static bool ValidateBasicInputsStatic(int nCount, const float* pOut, const std::string& functionName);

protected:
    /**
     * @brief Utility: Safe array copy with bounds checking
     * @param dest Destination array
     * @param src Source array
     * @param count Number of elements to copy
     * @return true if copy succeeded
     */
    static bool SafeArrayCopy(float* dest, const float* src, int count);

    /**
     * @brief Utility: Initialize output array with default value
     * @param pOut Output array
     * @param count Number of elements
     * @param defaultValue Default value to use (default: 0.0f)
     */
    static void InitializeOutput(float* pOut, int count, float defaultValue = 0.0f);

    /**
     * @brief Utility: Check if array pointer is valid for given count
     * @param ptr Array pointer
     * @param count Expected element count
     * @return true if pointer appears to be valid
     */
    static bool IsValidArrayPointer(const float* ptr, int count);

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
     * @param nCount Number of data points
     * @param hasA Whether input A is provided
     * @param hasB Whether input B is provided
     * @param hasC Whether input C is provided
     */
    static void LogFunctionCall(const std::string& functionName, int nCount, 
                               bool hasA, bool hasB, bool hasC);

    /**
     * @brief Get function instance from registry for logging/utilities
     * @param functionMark Function identifier
     * @return Function instance or nullptr if not found
     */
    static TdxFunctionPtr GetFunctionFromRegistry(unsigned short functionMark);

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

#endif // __TDX_FUNCTION_BASE_H__ 