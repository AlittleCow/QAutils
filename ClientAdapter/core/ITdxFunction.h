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
 * @brief Interface for TDX functions
 * 
 * This interface provides metadata and registration support for TDX functions.
 * The actual calculation is performed by the C-style function pointer that
 * TDX calls directly. This design aligns with how TDX actually works.
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
     * @brief Get function parameter information
     * @return Description of function parameters and usage
     */
    virtual std::string GetParameterInfo() const = 0;

    /**
     * @brief Get the C-style function pointer for TDX registration
     * 
     * This is the actual function that TDX will call directly.
     * It should contain all the calculation logic and error handling.
     * 
     * @return Function pointer that TDX will call
     */
    virtual pPluginFUNC GetCFunctionPointer() = 0;

    /**
     * @brief Validate if the function is properly configured
     * @return true if function is ready for registration
     */
    virtual bool IsValid() const = 0;

    /**
     * @brief Get function category for organization
     * @return Category string (e.g., "Technical", "Statistical", "Custom")
     */
    virtual std::string GetCategory() const = 0;

    /**
     * @brief Get minimum required input count
     * @return Minimum number of data points needed
     */
    virtual int GetMinInputCount() const = 0;

    /**
     * @brief Check if function supports variable input arrays
     * @return true if function can handle nullptr input arrays
     */
    virtual bool SupportsVariableInputs() const = 0;
};

/**
 * @brief Smart pointer type for TDX functions
 */
using TdxFunctionPtr = std::shared_ptr<ITdxFunction>;

/**
 * @brief Forward declaration of TdxFunctionRegistry
 * 
 * The complete TdxFunctionRegistry class is defined in TdxFunctionRegistry.h
 * Include that header when you need to use the registry.
 */
class TdxFunctionRegistry;

#endif // __ITDX_FUNCTION_H__ 