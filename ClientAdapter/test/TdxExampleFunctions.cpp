#include "TdxExampleFunctions.h"
#include <algorithm>
#include <numeric>
#include <limits>

// ============================================================================
// SequenceFunction Implementation
// ============================================================================

/**
 * @brief Constructor for SequenceFunction
 */
SequenceFunction::SequenceFunction()
    : TdxFunctionBase(1, "SequenceFunction", "Generates sequential values (0, 1, 2, 3, ...)")
{
}

/**
 * @brief Generate sequential values in output array
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Input array A (ignored)
 * @param pInB Input array B (ignored)
 * @param pInC Input array C (ignored)
 * @return true if calculation succeeded
 */
bool SequenceFunction::CalculateCore(int nCount, float* pOut, const float* pInA,
                                    const float* pInB, const float* pInC)
{
    for (int i = 0; i < nCount; ++i)
    {
        pOut[i] = static_cast<float>(i) * (*pInA + *pInB + *pInC);
    }
    
    LogDebug("Generated sequence of " + std::to_string(nCount) + " values");
    return true;
}

// ============================================================================
// AverageFunction Implementation
// ============================================================================

/**
 * @brief Constructor for AverageFunction
 */
AverageFunction::AverageFunction()
    : TdxFunctionBase(2, "AverageFunction", "Calculates average of three input arrays")
{
}

/**
 * @brief Validate inputs for average calculation
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Input array A
 * @param pInB Input array B
 * @param pInC Input array C
 * @return true if all required inputs are valid
 */
bool AverageFunction::ValidateInputs(int nCount, const float* pOut, const float* pInA,
                                    const float* pInB, const float* pInC) const
{
    // Call base validation first
    if (!TdxFunctionBase::ValidateInputs(nCount, pOut, pInA, pInB, pInC))
    {
        return false;
    }

    // Check that all input arrays are provided
    if (pInA == nullptr)
    {
        LogError("Input array A is required for average calculation");
        return false;
    }

    if (pInB == nullptr)
    {
        LogError("Input array B is required for average calculation");
        return false;
    }

    if (pInC == nullptr)
    {
        LogError("Input array C is required for average calculation");
        return false;
    }

    return true;
}

/**
 * @brief Calculate average of three input arrays
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Input array A
 * @param pInB Input array B
 * @param pInC Input array C
 * @return true if calculation succeeded
 */
bool AverageFunction::CalculateCore(int nCount, float* pOut, const float* pInA,
                                   const float* pInB, const float* pInC)
{
    for (int i = 0; i < nCount; ++i)
    {
        pOut[i] = (pInA[i] + pInB[i] + pInC[i]) / 3.0f;
    }
    
    LogDebug("Calculated average for " + std::to_string(nCount) + " data points");
    return true;
}

// ============================================================================
// SimpleMovingAverageFunction Implementation
// ============================================================================

/**
 * @brief Constructor for SimpleMovingAverageFunction
 */
SimpleMovingAverageFunction::SimpleMovingAverageFunction()
    : TdxFunctionBase(3, "SimpleMovingAverage", "Calculates Simple Moving Average (SMA)")
{
}

/**
 * @brief Validate inputs for SMA calculation
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Price data array
 * @param pInB Period parameter array
 * @param pInC Not used
 * @return true if inputs are valid
 */
bool SimpleMovingAverageFunction::ValidateInputs(int nCount, const float* pOut, const float* pInA,
                                                const float* pInB, const float* pInC) const
{
    // Call base validation
    if (!TdxFunctionBase::ValidateInputs(nCount, pOut, pInA, pInB, pInC))
    {
        return false;
    }

    if (pInA == nullptr)
    {
        LogError("Price data array (InA) is required for SMA calculation");
        return false;
    }

    if (pInB == nullptr)
    {
        LogError("Period parameter array (InB) is required for SMA calculation");
        return false;
    }

    int period = GetPeriod(pInB);
    if (period <= 0 || period > nCount)
    {
        LogError("Invalid SMA period: " + std::to_string(period));
        return false;
    }

    return true;
}

/**
 * @brief Calculate Simple Moving Average
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Price data array
 * @param pInB Period parameter array
 * @param pInC Not used
 * @return true if calculation succeeded
 */
bool SimpleMovingAverageFunction::CalculateCore(int nCount, float* pOut, const float* pInA,
                                               const float* pInB, const float* pInC)
{
    (void)pInC;
    int period = GetPeriod(pInB);
    
    // Initialize output array with NaN for values before sufficient data
    for (int i = 0; i < period - 1; ++i)
    {
        pOut[i] = std::numeric_limits<float>::quiet_NaN();
    }
    
    // Calculate SMA for remaining values
    for (int i = period - 1; i < nCount; ++i)
    {
        float sum = 0.0f;
        for (int j = i - period + 1; j <= i; ++j)
        {
            sum += pInA[j];
        }
        pOut[i] = sum / static_cast<float>(period);
    }
    
    LogDebug("Calculated SMA with period " + std::to_string(period) + 
             " for " + std::to_string(nCount) + " data points");
    return true;
}

/**
 * @brief Get period from parameter array
 * @param pInB Parameter array
 * @return Period value (default 5 if invalid)
 */
int SimpleMovingAverageFunction::GetPeriod(const float* pInB) const
{
    if (pInB == nullptr)
    {
        return 5; // Default period
    }
    
    int period = static_cast<int>(pInB[0]);
    return (period > 0) ? period : 5;
}

// ============================================================================
// ExponentialMovingAverageFunction Implementation
// ============================================================================

/**
 * @brief Constructor for ExponentialMovingAverageFunction
 */
ExponentialMovingAverageFunction::ExponentialMovingAverageFunction()
    : TdxFunctionBase(4, "ExponentialMovingAverage", "Calculates Exponential Moving Average (EMA)")
{
}

/**
 * @brief Validate inputs for EMA calculation
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Price data array
 * @param pInB Period parameter array
 * @param pInC Not used
 * @return true if inputs are valid
 */
bool ExponentialMovingAverageFunction::ValidateInputs(int nCount, const float* pOut, const float* pInA,
                                                     const float* pInB, const float* pInC) const
{
    // Call base validation
    if (!TdxFunctionBase::ValidateInputs(nCount, pOut, pInA, pInB, pInC))
    {
        return false;
    }

    if (pInA == nullptr)
    {
        LogError("Price data array (InA) is required for EMA calculation");
        return false;
    }

    if (pInB == nullptr)
    {
        LogError("Period parameter array (InB) is required for EMA calculation");
        return false;
    }

    int period = static_cast<int>(pInB[0]);
    if (period <= 0)
    {
        LogError("Invalid EMA period: " + std::to_string(period));
        return false;
    }

    return true;
}

/**
 * @brief Calculate Exponential Moving Average
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Price data array
 * @param pInB Period parameter array
 * @param pInC Not used
 * @return true if calculation succeeded
 */
bool ExponentialMovingAverageFunction::CalculateCore(int nCount, float* pOut, const float* pInA,
                                                    const float* pInB, const float* pInC)
{
    (void)pInC;
    int period = static_cast<int>(pInB[0]);
    float alpha = GetSmoothingFactor(period);
    
    if (nCount == 0)
    {
        return true;
    }
    
    // Initialize first value
    pOut[0] = pInA[0];
    
    // Calculate EMA for remaining values
    for (int i = 1; i < nCount; ++i)
    {
        pOut[i] = alpha * pInA[i] + (1.0f - alpha) * pOut[i - 1];
    }
    
    LogDebug("Calculated EMA with period " + std::to_string(period) + 
             " (alpha=" + std::to_string(alpha) + ") for " + std::to_string(nCount) + " data points");
    return true;
}

/**
 * @brief Calculate smoothing factor for EMA
 * @param period EMA period
 * @return Smoothing factor (alpha)
 */
float ExponentialMovingAverageFunction::GetSmoothingFactor(int period) const
{
    return 2.0f / (static_cast<float>(period) + 1.0f);
}

// ============================================================================
// DebugControlFunction Implementation
// ============================================================================

/**
 * @brief Constructor for DebugControlFunction
 */
DebugControlFunction::DebugControlFunction()
    : TdxFunctionBase(100, "DebugControl", "Enable/Disable debug mode at runtime")
{
}

/**
 * @brief Validate inputs for debug control
 * @param nCount Number of data points
 * @param pOut Output array
 * @param pInA Control parameter array
 * @param pInB Not used
 * @param pInC Not used
 * @return true if inputs are valid
 */
bool DebugControlFunction::ValidateInputs(int nCount, const float* pOut, const float* pInA,
                                         const float* pInB, const float* pInC) const
{
    // Suppress unused parameter warnings
    (void)pInB;
    (void)pInC;
    
    // Call base validation
    if (!TdxFunctionBase::ValidateInputs(nCount, pOut, pInA, pInB, pInC))
    {
        return false;
    }

    if (pInA == nullptr)
    {
        LogError("Control parameter array (InA) is required for debug control");
        return false;
    }

    return true;
}

/**
 * @brief Control debug mode and return status
 * @param nCount Number of data points
 * @param pOut Output array (debug status)
 * @param pInA Control parameter array
 * @param pInB Not used
 * @param pInC Not used
 * @return true if operation succeeded
 */
bool DebugControlFunction::CalculateCore(int nCount, float* pOut, const float* pInA,
                                        const float* pInB, const float* pInC)
{
    // Suppress unused parameter warnings
    (void)pInB;
    (void)pInC;
    
    // Get control parameter (1.0 = enable, 0.0 = disable)
    bool enableDebug = (pInA[0] >= 0.5f);
    
    // Set debug mode
    TdxFunctionBase::SetDebugMode(enableDebug);
    
    // Return current debug status in all output elements
    float debugStatus = TdxFunctionBase::IsDebugMode() ? 1.0f : 0.0f;
    for (int i = 0; i < nCount; ++i)
    {
        pOut[i] = debugStatus;
    }
    
    LogDebug("Debug mode " + std::string(enableDebug ? "enabled" : "disabled") + 
             " via TDX function call");
    
    return true;
} 