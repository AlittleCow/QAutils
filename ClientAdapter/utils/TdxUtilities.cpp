#include "TdxUtilities.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <algorithm>
#include <cstring>

// ============================================================================
// TdxUtilities Implementation
// ============================================================================

/**
 * @brief Validate array pointer and size
 * @param pArray Array pointer to validate
 * @param nSize Expected array size
 * @param arrayName Name of array for error messages
 * @return true if array is valid
 */
bool TdxUtilities::ValidateArray(const float* pArray, int nSize, const std::string& arrayName)
{
    if (pArray == nullptr)
    {
        std::cerr << "Array " << arrayName << " is null" << std::endl;
        return false;
    }

    if (nSize <= 0)
    {
        std::cerr << "Array " << arrayName << " has invalid size: " << nSize << std::endl;
        return false;
    }

    return true;
}

/**
 * @brief Check if a value is valid (not NaN or infinity)
 * @param value Value to check
 * @return true if value is valid
 */
bool TdxUtilities::IsValidValue(float value)
{
    return std::isfinite(value);
}

/**
 * @brief Fill array with specified value
 * @param pArray Array to fill
 * @param nSize Array size
 * @param value Value to fill with
 */
void TdxUtilities::FillArray(float* pArray, int nSize, float value)
{
    if (!ValidateArray(pArray, nSize, "FillArray"))
    {
        return;
    }

    std::fill(pArray, pArray + nSize, value);
}

/**
 * @brief Copy array data
 * @param pDest Destination array
 * @param pSrc Source array
 * @param nSize Number of elements to copy
 */
void TdxUtilities::CopyArray(float* pDest, const float* pSrc, int nSize)
{
    if (!ValidateArray(pDest, nSize, "CopyArray_Dest") || 
        !ValidateArray(pSrc, nSize, "CopyArray_Src"))
    {
        return;
    }

    std::memcpy(pDest, pSrc, nSize * sizeof(float));
}

/**
 * @brief Calculate sum of array elements
 * @param pArray Array to sum
 * @param nSize Array size
 * @return Sum of all elements
 */
float TdxUtilities::SumArray(const float* pArray, int nSize)
{
    if (!ValidateArray(pArray, nSize, "SumArray"))
    {
        return 0.0f;
    }

    float sum = 0.0f;
    for (int i = 0; i < nSize; ++i)
    {
        if (IsValidValue(pArray[i]))
        {
            sum += pArray[i];
        }
    }

    return sum;
}

/**
 * @brief Calculate mean of array elements
 * @param pArray Array to average
 * @param nSize Array size
 * @return Mean value
 */
float TdxUtilities::MeanArray(const float* pArray, int nSize)
{
    if (!ValidateArray(pArray, nSize, "MeanArray"))
    {
        return 0.0f;
    }

    float sum = SumArray(pArray, nSize);
    return sum / static_cast<float>(nSize);
}

/**
 * @brief Find minimum value in array
 * @param pArray Array to search
 * @param nSize Array size
 * @return Minimum value
 */
float TdxUtilities::MinArray(const float* pArray, int nSize)
{
    if (!ValidateArray(pArray, nSize, "MinArray"))
    {
        return 0.0f;
    }

    float minVal = pArray[0];
    for (int i = 1; i < nSize; ++i)
    {
        if (IsValidValue(pArray[i]) && pArray[i] < minVal)
        {
            minVal = pArray[i];
        }
    }

    return minVal;
}

/**
 * @brief Find maximum value in array
 * @param pArray Array to search
 * @param nSize Array size
 * @return Maximum value
 */
float TdxUtilities::MaxArray(const float* pArray, int nSize)
{
    if (!ValidateArray(pArray, nSize, "MaxArray"))
    {
        return 0.0f;
    }

    float maxVal = pArray[0];
    for (int i = 1; i < nSize; ++i)
    {
        if (IsValidValue(pArray[i]) && pArray[i] > maxVal)
        {
            maxVal = pArray[i];
        }
    }

    return maxVal;
}

/**
 * @brief Get current timestamp as string
 * @return Formatted timestamp string
 */
std::string TdxUtilities::GetTimeStamp()
{
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;

    std::ostringstream oss;
    oss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    oss << '.' << std::setfill('0') << std::setw(3) << ms.count();
    
    return oss.str();
}

/**
 * @brief Convert Windows error code to string
 * @param errorCode Windows error code
 * @return Error description string
 */
std::string TdxUtilities::GetErrorString(DWORD errorCode)
{
    LPSTR messageBuffer = nullptr;
    DWORD size = FormatMessageA(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
        nullptr, errorCode, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPSTR)&messageBuffer, 0, nullptr);

    std::string message(messageBuffer, size);
    LocalFree(messageBuffer);
    
    return message;
}

/**
 * @brief Safe division with infinity check
 * @param numerator Numerator value
 * @param denominator Denominator value
 * @param defaultValue Default value if division is invalid
 * @return Division result or default value
 */
float TdxUtilities::SafeDivide(float numerator, float denominator, float defaultValue)
{
    if (std::abs(denominator) < std::numeric_limits<float>::epsilon())
    {
        return defaultValue;
    }

    float result = numerator / denominator;
    return IsValidValue(result) ? result : defaultValue;
}

/**
 * @brief Linear interpolation between two values
 * @param value1 First value
 * @param value2 Second value
 * @param factor Interpolation factor (0.0 to 1.0)
 * @return Interpolated value
 */
float TdxUtilities::LinearInterpolate(float value1, float value2, float factor)
{
    factor = ClampValue(factor, 0.0f, 1.0f);
    return value1 + factor * (value2 - value1);
}

/**
 * @brief Clamp value to specified range
 * @param value Value to clamp
 * @param minValue Minimum allowed value
 * @param maxValue Maximum allowed value
 * @return Clamped value
 */
float TdxUtilities::ClampValue(float value, float minValue, float maxValue)
{
    if (value < minValue) return minValue;
    if (value > maxValue) return maxValue;
    return value;
}

// ============================================================================
// TdxPerformanceTimer Implementation
// ============================================================================

/**
 * @brief Constructor - initializes the timer
 */
TdxPerformanceTimer::TdxPerformanceTimer()
    : m_running(false)
{
    QueryPerformanceFrequency(&m_frequency);
    m_startTime.QuadPart = 0;
    m_endTime.QuadPart = 0;
}

/**
 * @brief Start timing
 */
void TdxPerformanceTimer::Start()
{
    m_running = true;
    QueryPerformanceCounter(&m_startTime);
}

/**
 * @brief Stop timing
 */
void TdxPerformanceTimer::Stop()
{
    if (m_running)
    {
        QueryPerformanceCounter(&m_endTime);
        m_running = false;
    }
}

/**
 * @brief Get elapsed time in milliseconds
 * @return Elapsed time in milliseconds
 */
double TdxPerformanceTimer::GetElapsedMilliseconds() const
{
    if (m_running)
    {
        LARGE_INTEGER currentTime;
        QueryPerformanceCounter(&currentTime);
        return static_cast<double>(currentTime.QuadPart - m_startTime.QuadPart) * 1000.0 / 
               static_cast<double>(m_frequency.QuadPart);
    }
    else
    {
        return static_cast<double>(m_endTime.QuadPart - m_startTime.QuadPart) * 1000.0 / 
               static_cast<double>(m_frequency.QuadPart);
    }
}

/**
 * @brief Get elapsed time in microseconds
 * @return Elapsed time in microseconds
 */
double TdxPerformanceTimer::GetElapsedMicroseconds() const
{
    return GetElapsedMilliseconds() * 1000.0;
}

/**
 * @brief Check if timer is currently running
 * @return true if timer is running
 */
bool TdxPerformanceTimer::IsRunning() const
{
    return m_running;
}

/**
 * @brief Reset the timer
 */
void TdxPerformanceTimer::Reset()
{
    m_running = false;
    m_startTime.QuadPart = 0;
    m_endTime.QuadPart = 0;
}

// ============================================================================
// TdxAutoTimer Implementation
// ============================================================================

/**
 * @brief Constructor - starts timing
 * @param name Name for the timer (used in output)
 */
TdxAutoTimer::TdxAutoTimer(const std::string& name)
    : m_name(name)
{
    m_timer.Start();
}

/**
 * @brief Destructor - stops timing and outputs result
 */
TdxAutoTimer::~TdxAutoTimer()
{
    m_timer.Stop();
    std::cout << "[TIMER] " << m_name << ": " 
              << m_timer.GetElapsedMilliseconds() << " ms" << std::endl;
} 