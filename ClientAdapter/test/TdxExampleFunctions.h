#ifndef __TDX_EXAMPLE_FUNCTIONS_H__
#define __TDX_EXAMPLE_FUNCTIONS_H__

#include "TdxFunctionBase.h"
#include <cmath>

/**
 * @brief Example function that generates a simple sequence (0, 1, 2, 3, ...)
 * 
 * This function demonstrates basic TDX function implementation.
 * It ignores input arrays and generates a simple sequential output.
 */
class SequenceFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    SequenceFunction();

    /**
     * @brief Destructor
     */
    virtual ~SequenceFunction() = default;

protected:
    /**
     * @brief Generate sequential values
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Input array A (ignored)
     * @param pInB Input array B (ignored)
     * @param pInC Input array C (ignored)
     * @return true if calculation succeeded
     */
    bool CalculateCore(int nCount, float* pOut, const float* pInA,
                      const float* pInB, const float* pInC) override;
};

/**
 * @brief Example function that calculates average of three input arrays
 * 
 * This function demonstrates how to use multiple input arrays.
 * Output[i] = (InA[i] + InB[i] + InC[i]) / 3
 */
class AverageFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    AverageFunction();

    /**
     * @brief Destructor
     */
    virtual ~AverageFunction() = default;

    /**
     * @brief Validate inputs for average calculation
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Input array A
     * @param pInB Input array B
     * @param pInC Input array C
     * @return true if all input arrays are valid
     */
    bool ValidateInputs(int nCount, const float* pOut, const float* pInA,
                       const float* pInB, const float* pInC) const override;

protected:
    /**
     * @brief Calculate average of three arrays
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Input array A (required)
     * @param pInB Input array B (required)
     * @param pInC Input array C (required)
     * @return true if calculation succeeded
     */
    bool CalculateCore(int nCount, float* pOut, const float* pInA,
                      const float* pInB, const float* pInC) override;
};

/**
 * @brief Example function that calculates Simple Moving Average (SMA)
 * 
 * This function demonstrates more complex calculation logic.
 * It uses the first input array as price data and calculates SMA.
 * The period is determined by the second input array's first value.
 */
class SimpleMovingAverageFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    SimpleMovingAverageFunction();

    /**
     * @brief Destructor
     */
    virtual ~SimpleMovingAverageFunction() = default;

    /**
     * @brief Validate inputs for SMA calculation
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Price data array (required)
     * @param pInB Period parameter (required, uses first value)
     * @param pInC Not used
     * @return true if inputs are valid
     */
    bool ValidateInputs(int nCount, const float* pOut, const float* pInA,
                       const float* pInB, const float* pInC) const override;

protected:
    /**
     * @brief Calculate Simple Moving Average
     * @param nCount Number of data points
     * @param pOut Output array (SMA values)
     * @param pInA Price data array
     * @param pInB Period parameter array (uses first value)
     * @param pInC Not used
     * @return true if calculation succeeded
     */
    bool CalculateCore(int nCount, float* pOut, const float* pInA,
                      const float* pInB, const float* pInC) override;

private:
    /**
     * @brief Get the period from parameter array
     * @param pInB Parameter array
     * @return Period value (default 5 if invalid)
     */
    int GetPeriod(const float* pInB) const;
};

/**
 * @brief Example function that calculates Exponential Moving Average (EMA)
 * 
 * This function demonstrates advanced calculation with state management.
 */
class ExponentialMovingAverageFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    ExponentialMovingAverageFunction();

    /**
     * @brief Destructor
     */
    virtual ~ExponentialMovingAverageFunction() = default;

    /**
     * @brief Validate inputs for EMA calculation
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Price data array (required)
     * @param pInB Period parameter (required)
     * @param pInC Not used
     * @return true if inputs are valid
     */
    bool ValidateInputs(int nCount, const float* pOut, const float* pInA,
                       const float* pInB, const float* pInC) const override;

protected:
    /**
     * @brief Calculate Exponential Moving Average
     * @param nCount Number of data points
     * @param pOut Output array (EMA values)
     * @param pInA Price data array
     * @param pInB Period parameter array
     * @param pInC Not used
     * @return true if calculation succeeded
     */
    bool CalculateCore(int nCount, float* pOut, const float* pInA,
                      const float* pInB, const float* pInC) override;

private:
    /**
     * @brief Calculate smoothing factor
     * @param period EMA period
     * @return Smoothing factor (alpha)
     */
    float GetSmoothingFactor(int period) const;
};

/**
 * @brief Debug control function for runtime debug mode management
 * 
 * This function allows users to enable/disable debug mode at runtime.
 * Usage: Call with pInA[0] = 1.0 to enable debug, 0.0 to disable
 * Returns current debug status in pOut[0] (1.0 = enabled, 0.0 = disabled)
 */
class DebugControlFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    DebugControlFunction();

    /**
     * @brief Destructor
     */
    virtual ~DebugControlFunction() = default;

    /**
     * @brief Validate inputs for debug control
     * @param nCount Number of data points
     * @param pOut Output array
     * @param pInA Control parameter (1.0 = enable, 0.0 = disable)
     * @param pInB Not used
     * @param pInC Not used
     * @return true if inputs are valid
     */
    bool ValidateInputs(int nCount, const float* pOut, const float* pInA,
                       const float* pInB, const float* pInC) const override;

protected:
    /**
     * @brief Control debug mode and return status
     * @param nCount Number of data points
     * @param pOut Output array (debug status)
     * @param pInA Control parameter array
     * @param pInB Not used
     * @param pInC Not used
     * @return true if operation succeeded
     */
    bool CalculateCore(int nCount, float* pOut, const float* pInA,
                      const float* pInB, const float* pInC) override;
};

#endif // __TDX_EXAMPLE_FUNCTIONS_H__ 