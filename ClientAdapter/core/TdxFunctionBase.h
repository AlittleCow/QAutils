#ifndef __TDX_FUNCTION_BASE_H__
#define __TDX_FUNCTION_BASE_H__

#include "ITdxFunction.h"
#include <stdexcept>
#include <sstream>

/**
 * @brief Base implementation class for TDX functions
 * 
 * This class provides common functionality and default implementations
 * for most ITdxFunction methods. Derived classes only need to implement
 * the core calculation logic.
 */
class TdxFunctionBase : public ITdxFunction
{
protected:
    unsigned short m_functionMark;  /**< Function identifier */
    std::string m_functionName;     /**< Function name */
    std::string m_description;      /**< Function description */
    
    static bool s_debugMode;        /**< Global debug mode flag */

public:
    /**
     * @brief Constructor
     * @param functionMark Unique function identifier for TDX
     * @param functionName Human-readable function name
     * @param description Function description
     */
    TdxFunctionBase(unsigned short functionMark, 
                   const std::string& functionName,
                   const std::string& description);

    /**
     * @brief Destructor
     */
    virtual ~TdxFunctionBase() = default;

    // ITdxFunction interface implementation
    unsigned short GetFunctionMark() const override;
    std::string GetFunctionName() const override;
    std::string GetDescription() const override;
    
    /**
     * @brief Default input validation
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Input array A
     * @param pInB Input array B
     * @param pInC Input array C
     * @return true if basic validation passes
     */
    bool ValidateInputs(int nCount, const float* pOut, const float* pInA,
                       const float* pInB, const float* pInC) const override;

    /**
     * @brief Get C-style function pointer with error handling wrapper
     * @return Function pointer for TDX registration
     */
    pPluginFUNC GetCFunctionPointer() override;

    /**
     * @brief Execute the function with error handling
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Input array A
     * @param pInB Input array B
     * @param pInC Input array C
     * @return true if execution succeeded
     */
    bool Execute(int nCount, float* pOut, const float* pInA,
                const float* pInB, const float* pInC);

    /**
     * @brief Enable or disable debug mode globally
     * @param enable true to enable debug logging, false to disable
     */
    static void SetDebugMode(bool enable);

    /**
     * @brief Check if debug mode is enabled
     * @return true if debug mode is enabled
     */
    static bool IsDebugMode();

    /**
     * @brief Set current instance for C wrapper access
     */
    void SetCurrentInstance();

protected:
    /**
     * @brief Core calculation implementation (must be overridden)
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Input array A
     * @param pInB Input array B
     * @param pInC Input array C
     * @return true if calculation succeeded
     */
    virtual bool CalculateCore(int nCount, float* pOut, const float* pInA,
                              const float* pInB, const float* pInC) = 0;

    /**
     * @brief Log error message (can be overridden for custom logging)
     * @param message Error message
     */
    virtual void LogError(const std::string& message) const;

    /**
     * @brief Log debug message (can be overridden for custom logging)
     * @param message Debug message
     */
    virtual void LogDebug(const std::string& message) const;

private:
    /**
     * @brief Static C-style wrapper function
     * This is the actual function pointer that gets registered with TDX
     */
    static void CStyleWrapper(int nCount, float* pOut, float* pInA, float* pInB, float* pInC);
    
    /**
     * @brief Store reference to current instance for C wrapper
     */
    static thread_local TdxFunctionBase* s_currentInstance;
};

#endif // __TDX_FUNCTION_BASE_H__ 