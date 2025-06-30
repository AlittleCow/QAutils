#ifndef __TDX_UTILITIES_H__
#define __TDX_UTILITIES_H__

#include <vector>
#include <string>
#include <cmath>
#include <windows.h>

/**
 * @brief Utility class for TDX data validation and common operations
 */
class TdxUtilities
{
public:
    /**
     * @brief Validate array pointer and size
     * @param pArray Array pointer to validate
     * @param nSize Expected array size
     * @param arrayName Name of array for error messages
     * @return true if array is valid
     */
    static bool ValidateArray(const float* pArray, int nSize, const std::string& arrayName);

    /**
     * @brief Check if a value is valid (not NaN or infinity)
     * @param value Value to check
     * @return true if value is valid
     */
    static bool IsValidValue(float value);

    /**
     * @brief Fill array with specified value
     * @param pArray Array to fill
     * @param nSize Array size
     * @param value Value to fill with
     */
    static void FillArray(float* pArray, int nSize, float value);

    /**
     * @brief Copy array data
     * @param pDest Destination array
     * @param pSrc Source array
     * @param nSize Number of elements to copy
     */
    static void CopyArray(float* pDest, const float* pSrc, int nSize);

    /**
     * @brief Calculate sum of array elements
     * @param pArray Array to sum
     * @param nSize Array size
     * @return Sum of all elements
     */
    static float SumArray(const float* pArray, int nSize);

    /**
     * @brief Calculate mean of array elements
     * @param pArray Array to average
     * @param nSize Array size
     * @return Mean value
     */
    static float MeanArray(const float* pArray, int nSize);

    /**
     * @brief Find minimum value in array
     * @param pArray Array to search
     * @param nSize Array size
     * @return Minimum value
     */
    static float MinArray(const float* pArray, int nSize);

    /**
     * @brief Find maximum value in array
     * @param pArray Array to search
     * @param nSize Array size
     * @return Maximum value
     */
    static float MaxArray(const float* pArray, int nSize);

    /**
     * @brief Get current timestamp as string
     * @return Formatted timestamp string
     */
    static std::string GetTimeStamp();

    /**
     * @brief Convert Windows error code to string
     * @param errorCode Windows error code
     * @return Error description string
     */
    static std::string GetErrorString(DWORD errorCode);

    /**
     * @brief Safe division with infinity check
     * @param numerator Numerator value
     * @param denominator Denominator value
     * @param defaultValue Default value if division is invalid
     * @return Division result or default value
     */
    static float SafeDivide(float numerator, float denominator, float defaultValue = 0.0f);

    /**
     * @brief Linear interpolation between two values
     * @param value1 First value
     * @param value2 Second value
     * @param factor Interpolation factor (0.0 to 1.0)
     * @return Interpolated value
     */
    static float LinearInterpolate(float value1, float value2, float factor);

    /**
     * @brief Clamp value to specified range
     * @param value Value to clamp
     * @param minValue Minimum allowed value
     * @param maxValue Maximum allowed value
     * @return Clamped value
     */
    static float ClampValue(float value, float minValue, float maxValue);
};

/**
 * @brief Performance timer for measuring execution time
 */
class TdxPerformanceTimer
{
private:
    LARGE_INTEGER m_frequency;
    LARGE_INTEGER m_startTime;
    LARGE_INTEGER m_endTime;
    bool m_running;

public:
    /**
     * @brief Constructor - initializes the timer
     */
    TdxPerformanceTimer();

    /**
     * @brief Start timing
     */
    void Start();

    /**
     * @brief Stop timing
     */
    void Stop();

    /**
     * @brief Get elapsed time in milliseconds
     * @return Elapsed time in milliseconds
     */
    double GetElapsedMilliseconds() const;

    /**
     * @brief Get elapsed time in microseconds
     * @return Elapsed time in microseconds
     */
    double GetElapsedMicroseconds() const;

    /**
     * @brief Check if timer is currently running
     * @return true if timer is running
     */
    bool IsRunning() const;

    /**
     * @brief Reset the timer
     */
    void Reset();
};

/**
 * @brief Automatic performance measurement with RAII
 */
class TdxAutoTimer
{
private:
    TdxPerformanceTimer m_timer;
    std::string m_name;

public:
    /**
     * @brief Constructor - starts timing
     * @param name Name for the timer (used in output)
     */
    explicit TdxAutoTimer(const std::string& name);

    /**
     * @brief Destructor - stops timing and outputs result
     */
    ~TdxAutoTimer();
};

/**
 * @brief Macro for easy performance measurement
 */
#define TDX_MEASURE_PERFORMANCE(name) TdxAutoTimer _timer(name)

#endif // __TDX_UTILITIES_H__ 