#ifndef __ITDX_FUNCTION_H__
#define __ITDX_FUNCTION_H__

#include <windows.h>
#include <string>
#include <vector>
#include <memory>

#pragma pack(push, 1)

/**
 * @brief Function signature for TDX plugin functions
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Input array A
 * @param pInB Input array B  
 * @param pInC Input array C
 */
typedef void(*pPluginFUNC)(int nCount, float* pOut, float* pInA, float* pInB, float* pInC);

/**
 * @brief Structure for TDX function information
 */
typedef struct tagPluginTCalcFuncInfo
{
    unsigned short nFuncMark;  /**< Function identifier */
    pPluginFUNC pCallFunc;     /**< Function pointer */
} PluginTCalcFuncInfo;

#pragma pack(pop)

/**
 * @brief Abstract base interface for all TDX functions
 * 
 * This interface defines the contract that all TDX functions must implement.
 * It provides a clean OOP abstraction while maintaining compatibility with
 * the C-style TDX plugin interface.
 */
class ITdxFunction
{
public:
    virtual ~ITdxFunction() = default;

    /**
     * @brief Get the unique function identifier
     * @return Function mark/ID used by TDX
     */
    virtual unsigned short GetFunctionMark() const = 0;

    /**
     * @brief Get the function name for debugging/logging
     * @return Human-readable function name
     */
    virtual std::string GetFunctionName() const = 0;

    /**
     * @brief Get function description
     * @return Description of what the function does
     */
    virtual std::string GetDescription() const = 0;

    /**
     * @brief Execute the function calculation
     * @param nCount Number of data points
     * @param pOut Output array (must be pre-allocated)
     * @param pInA Input array A (can be nullptr if not used)
     * @param pInB Input array B (can be nullptr if not used)
     * @param pInC Input array C (can be nullptr if not used)
     * @return true if calculation succeeded, false otherwise
     */
    virtual bool Execute(int nCount, float* pOut, const float* pInA, 
                        const float* pInB, const float* pInC) = 0;

    /**
     * @brief Validate input parameters before execution
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Input array A
     * @param pInB Input array B
     * @param pInC Input array C
     * @return true if parameters are valid, false otherwise
     */
    virtual bool ValidateInputs(int nCount, const float* pOut, const float* pInA,
                               const float* pInB, const float* pInC) const = 0;

    /**
     * @brief Get the C-style function pointer for TDX compatibility
     * @return Function pointer that can be registered with TDX
     */
    virtual pPluginFUNC GetCFunctionPointer() = 0;
};

/**
 * @brief Smart pointer type for TDX functions
 */
using TdxFunctionPtr = std::shared_ptr<ITdxFunction>;

#endif // __ITDX_FUNCTION_H__ 