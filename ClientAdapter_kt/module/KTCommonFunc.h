#ifndef __KT_COMMON_FUNC_H__
#define __KT_COMMON_FUNC_H__

#include "../core/KTFunctionBase.h"
#include "../core/KTFunctionRegistry.h"
#include <map>
#include <string>
#include <vector>
#include <memory>
#include <mutex>

// KT Function ID offset for common functions
extern const int KT_COMMON_FUNCTION_ID_OFFSET;

/**
 * @brief Single Kbar data structure holding OHLCV information for KT
 */
struct KTKbarData
{
    float open;         /**< Open price */
    float high;         /**< High price */
    float low;          /**< Low price */
    float close;        /**< Close price */
    float volume;       /**< Volume */
    float amount;       /**< Amount */
    int date;           /**< Date in YYYYMMDD format */
    int time;           /**< Time in HHMMSS format */
    
    /**
     * @brief Default constructor
     */
    KTKbarData();
    
    /**
     * @brief Constructor with OHLCV data
     * @param o Open price
     * @param h High price
     * @param l Low price
     * @param c Close price
     * @param v Volume
     * @param a Amount
     */
    KTKbarData(float o, float h, float l, float c, float v, float a = 0.0f);
    
    /**
     * @brief Set date and time information
     * @param d Date in YYYYMMDD format
     * @param t Time in HHMMSS format
     */
    void SetDateTime(int d, int t);
    
    /**
     * @brief Convert to STKDATA format for KT compatibility
     * @param stkData Output STKDATA structure
     */
    void ToSTKDATA(STKDATA& stkData) const;
    
    /**
     * @brief Create from STKDATA format
     * @param stkData Input STKDATA structure
     */
    void FromSTKDATA(const STKDATA& stkData);
};

/**
 * @brief Key structure for identifying different symbol and period combinations
 */
struct KTKbarKey
{
    std::string symbol;     /**< Symbol name */
    std::string period;     /**< Period (e.g., "1min", "5min", "daily") */
    
    /**
     * @brief Constructor
     * @param sym Symbol name
     * @param per Period string
     */
    KTKbarKey(const std::string& sym, const std::string& per);
    
    /**
     * @brief Less-than operator for map ordering
     * @param other Other KTKbarKey to compare
     * @return true if this key is less than other
     */
    bool operator<(const KTKbarKey& other) const;
};

/**
 * @brief Manager class for maintaining Kbar data for different symbols and periods
 */
class KTKbarManager
{
private:
    std::map<KTKbarKey, std::vector<KTKbarData>> m_kbarData;  /**< Map of Kbar data by symbol/period */
    static std::unique_ptr<KTKbarManager> s_instance;         /**< Singleton instance */
    mutable std::mutex m_mutex;                               /**< Thread safety mutex */
    
    /**
     * @brief Private constructor for singleton pattern
     */
    KTKbarManager();

public:
    /**
     * @brief Get singleton instance
     * @return Reference to the singleton KTKbarManager instance
     */
    static KTKbarManager& GetInstance();
    
    /**
     * @brief Cleanup singleton instance
     */
    static void Cleanup();
    
    /**
     * @brief Add Kbar data for a specific symbol and period
     * @param symbol Symbol name
     * @param period Period string
     * @param kbar Kbar data to add
     */
    void AddKbar(const std::string& symbol, const std::string& period, const KTKbarData& kbar);
    
    /**
     * @brief Get Kbar data for a specific symbol and period
     * @param symbol Symbol name
     * @param period Period string
     * @return Const reference to vector of Kbar data
     */
    const std::vector<KTKbarData>& GetKbarData(const std::string& symbol, const std::string& period) const;
    
    /**
     * @brief Set complete Kbar data from CALCINFO
     * @param pCalcInfo CALCINFO structure containing K-line data
     * @param symbol Symbol name
     * @param period Period string
     */
    void SetKbarFromCALCINFO(const CALCINFO* pCalcInfo, const std::string& symbol, const std::string& period);
    
    /**
     * @brief Clear all Kbar data for a specific symbol and period
     * @param symbol Symbol name
     * @param period Period string
     */
    void ClearKbarData(const std::string& symbol, const std::string& period);
    
    /**
     * @brief Clear all Kbar data
     */
    void ClearAllData();
    
    /**
     * @brief Get number of Kbar records for a specific symbol and period
     * @param symbol Symbol name
     * @param period Period string
     * @return Number of Kbar records
     */
    int GetKbarCount(const std::string& symbol, const std::string& period) const;
    
    /**
     * @brief Debug function to log all available data in KTKbarManager
     */
    void DebugLogAllData() const;
};

/**
 * @brief Simple Moving Average (SMA) calculation function
 */
class KTSMAFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTSMAFunction();
    
    /**
     * @brief Get KT function pointer
     * @return Function pointer for KT registration
     */
    pKTFUNC GetKTFunctionPointer() const override;
    
    /**
     * @brief Static C-style function for KT
     * @param pCalcInfo CALCINFO structure
     * @return TRUE if successful, FALSE otherwise
     */
    static BOOL KT_CalculateSMA(CALCINFO* pCalcInfo);
};

/**
 * @brief Exponential Moving Average (EMA) calculation function
 */
class KTEMAFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTEMAFunction();
    
    /**
     * @brief Get KT function pointer
     * @return Function pointer for KT registration
     */
    pKTFUNC GetKTFunctionPointer() const override;
    
    /**
     * @brief Static C-style function for KT
     * @param pCalcInfo CALCINFO structure
     * @return TRUE if successful, FALSE otherwise
     */
    static BOOL KT_CalculateEMA(CALCINFO* pCalcInfo);
};

/**
 * @brief MACD (Moving Average Convergence Divergence) calculation function
 */
class KTMACDFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTMACDFunction();
    
    /**
     * @brief Get KT function pointer
     * @return Function pointer for KT registration
     */
    pKTFUNC GetKTFunctionPointer() const override;
    
    /**
     * @brief Static C-style function for KT
     * @param pCalcInfo CALCINFO structure
     * @return TRUE if successful, FALSE otherwise
     */
    static BOOL KT_CalculateMACD(CALCINFO* pCalcInfo);
};

/**
 * @brief RSI (Relative Strength Index) calculation function
 */
class KTRSIFunction : public KTFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    KTRSIFunction();
    
    /**
     * @brief Get KT function pointer
     * @return Function pointer for KT registration
     */
    pKTFUNC GetKTFunctionPointer() const override;
    
    /**
     * @brief Static C-style function for KT
     * @param pCalcInfo CALCINFO structure
     * @return TRUE if successful, FALSE otherwise
     */
    static BOOL KT_CalculateRSI(CALCINFO* pCalcInfo);
};

/**
 * @brief Utility functions for technical analysis
 */
namespace KTTechnicalUtils
{
    /**
     * @brief Calculate Simple Moving Average
     * @param data Input price data
     * @param period Moving average period
     * @param output Output array for SMA values
     * @param count Number of data points
     * @return true if calculation successful
     */
    bool CalculateSMA(const float* data, int period, float* output, int count);
    
    /**
     * @brief Calculate Exponential Moving Average
     * @param data Input price data
     * @param period EMA period
     * @param output Output array for EMA values
     * @param count Number of data points
     * @return true if calculation successful
     */
    bool CalculateEMA(const float* data, int period, float* output, int count);
    
    /**
     * @brief Calculate MACD indicator
     * @param data Input price data
     * @param fastPeriod Fast EMA period (default: 12)
     * @param slowPeriod Slow EMA period (default: 26)
     * @param signalPeriod Signal line period (default: 9)
     * @param macdLine Output MACD line
     * @param signalLine Output signal line
     * @param histogram Output histogram
     * @param count Number of data points
     * @return true if calculation successful
     */
    bool CalculateMACD(const float* data, int fastPeriod, int slowPeriod, int signalPeriod,
                       float* macdLine, float* signalLine, float* histogram, int count);
    
    /**
     * @brief Calculate RSI indicator
     * @param data Input price data
     * @param period RSI period (default: 14)
     * @param output Output array for RSI values
     * @param count Number of data points
     * @return true if calculation successful
     */
    bool CalculateRSI(const float* data, int period, float* output, int count);
    
    /**
     * @brief Extract close prices from CALCINFO
     * @param pCalcInfo CALCINFO structure
     * @param output Output array for close prices
     * @param maxCount Maximum number of prices to extract
     * @return Number of prices extracted
     */
    int ExtractClosePrices(const CALCINFO* pCalcInfo, float* output, int maxCount);
    
    /**
     * @brief Get parameter value from CALCINFO
     * @param pCalcInfo CALCINFO structure
     * @param paramIndex Parameter index (0-based)
     * @param defaultValue Default value if parameter not available
     * @return Parameter value
     */
    float GetParameter(const CALCINFO* pCalcInfo, int paramIndex, float defaultValue);
}

/**
 * @brief Register all KT common functions with the function registry
 * @return true if all functions were registered successfully
 */
bool RegisterKTCommonFunctions();

#endif // __KT_COMMON_FUNC_H__