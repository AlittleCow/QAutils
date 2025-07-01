#ifndef __TDX_COMMON_FUNC_H__
#define __TDX_COMMON_FUNC_H__

#include "TdxFunctionBase.h"
#include "../core/TdxFunctionRegistry.h"
#include <map>
#include <string>
#include <vector>
#include <memory>

/**
 * @brief Single Kbar data structure holding OHLCV information
 */
struct KbarData
{
    float open;         /**< Open price */
    float high;         /**< High price */
    float low;          /**< Low price */
    float close;        /**< Close price */
    long volume;        /**< Volume */
    short year;         /**< Year */
    char month;         /**< Month */
    char day;           /**< Day */
    char hour;          /**< Hour */
    char minute;        /**< Minute */
    
    /**
     * @brief Default constructor
     */
    KbarData();
    
    /**
     * @brief Constructor with OHLCV data
     * @param o Open price
     * @param h High price
     * @param l Low price
     * @param c Close price
     * @param v Volume
     */
    KbarData(float o, float h, float l, float c, long v);
    
    /**
     * @brief Set date information
     * @param y Year
     * @param m Month
     * @param d Day
     */
    void SetDate(short y, char m, char d);
    
    /**
     * @brief Set time information
     * @param h Hour
     * @param min Minute
     */
    void SetTime(char h, char min);
};

/**
 * @brief Key structure for identifying different symbol and period combinations
 */
struct KbarKey
{
    std::string symbol;     /**< Symbol name */
    std::string period;     /**< Period (e.g., "1min", "5min", "daily") */
    
    /**
     * @brief Constructor
     * @param sym Symbol name
     * @param per Period string
     */
    KbarKey(const std::string& sym, const std::string& per);
    
    /**
     * @brief Less-than operator for map ordering
     * @param other Other KbarKey to compare
     * @return true if this key is less than other
     */
    bool operator<(const KbarKey& other) const;
};

/**
 * @brief Manager class for maintaining Kbar data for different symbols and periods
 */
class KbarManager
{
private:
    std::map<KbarKey, std::vector<KbarData>> m_kbarData;  /**< Map of Kbar data by symbol/period */
    static std::unique_ptr<KbarManager> s_instance;       /**< Singleton instance */
    
    /**
     * @brief Private constructor for singleton pattern
     */
    KbarManager();

public:
    /**
     * @brief Get singleton instance
     * @return Reference to the singleton KbarManager instance
     */
    static KbarManager& GetInstance();
    
    /**
     * @brief Add Kbar data for a specific symbol and period
     * @param symbol Symbol name
     * @param period Period string
     * @param kbar Kbar data to add
     */
    void AddKbar(const std::string& symbol, const std::string& period, const KbarData& kbar);
    
    /**
     * @brief Get Kbar data for a specific symbol and period
     * @param symbol Symbol name
     * @param period Period string
     * @return Const reference to vector of Kbar data
     */
    const std::vector<KbarData>& GetKbarData(const std::string& symbol, const std::string& period) const;
    
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
     * @brief Debug function to log all available data in KbarManager
     */
    void DebugLogAllData() const;
    
    /**
     * @brief Set complete Kbar data arrays for a symbol and period
     * @param symbol Symbol name
     * @param period Period string
     * @param count Number of data points
     * @param openArray Array of open prices
     * @param highArray Array of high prices
     * @param lowArray Array of low prices
     * @param closeArray Array of close prices
     * @param volumeArray Array of volumes
     * @param yearArray Array of years
     * @param monthArray Array of months
     * @param dayArray Array of days
     * @param hourArray Array of hours
     * @param minuteArray Array of minutes
     */
    void SetKbarArrays(const std::string& symbol, const std::string& period, int count,
                       const float* openArray, const float* highArray, const float* lowArray,
                       const float* closeArray, const long* volumeArray,
                       const short* yearArray, const char* monthArray, const char* dayArray,
                       const char* hourArray, const char* minuteArray);
};

/**
 * @brief TDX API function to set OHLC data for Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (not used in this function)
 * @param pfINa Input array A (Open prices)
 * @param pfINb Input array B (High prices) 
 * @param pfINc Input array C (Low prices)
 */
TDX_EXPORT(TdxKbar_SetOHLC);

/**
 * @brief TDX API function to set Close and Volume data for Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (not used in this function)
 * @param pfINa Input array A (Close prices)
 * @param pfINb Input array B (Volume data)
 * @param pfINc Input array C (not used)
 */
TDX_EXPORT(TdxKbar_SetCloseVolume);

/**
 * @brief TDX API function to set date information for Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (not used in this function)
 * @param pfINa Input array A (Year)
 * @param pfINb Input array B (Month)
 * @param pfINc Input array C (Day)
 */
TDX_EXPORT(TdxKbar_SetDate);

/**
 * @brief TDX API function to set time information for Kbar and finalize data
 * @param DataLen Number of data points
 * @param pfOUT Output array (not used in this function)
 * @param pfINa Input array A (Hour)
 * @param pfINb Input array B (Minute)
 * @param pfINc Input array C (Symbol and period encoded as float)
 */
TDX_EXPORT(TdxKbar_SetTimeAndFinalize);

/**
 * @brief TDX API function to get OHLC data from Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (OHLC data encoded)
 * @param pfINa Input array A (Symbol and period encoded)
 * @param pfINb Input array B (Data type: 0=Open, 1=High, 2=Low, 3=Close)
 * @param pfINc Input array C (Index offset)
 */
TDX_EXPORT(TdxKbar_GetOHLC);

/**
 * @brief TDX API function to get Volume data from Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (Volume data)
 * @param pfINa Input array A (Symbol and period encoded)
 * @param pfINb Input array B (not used)
 * @param pfINc Input array C (Index offset)
 */
TDX_EXPORT(TdxKbar_GetVolume);

/**
 * @brief Helper function to encode symbol and period into float for TDX compatibility  
 * @param symbol Symbol string
 * @param period Period string
 * @return Encoded float value
 */
float EncodeSymbolPeriod(const std::string& symbol, const std::string& period);

/**
 * @brief Helper function to decode symbol and period from float
 * @param encoded Encoded float value
 * @param symbol Output symbol string
 * @param period Output period string
 */
void DecodeSymbolPeriod(float encoded, std::string& symbol, std::string& period);

/**
 * @brief Convert period code or string to standard period string format  
 * @param period Period code (as string) or period string to convert
 * @return Standard period string (e.g., "1min", "5min", "daily", etc.)
 */
std::string ConvertPeriodToStr(const std::string& period);

/**
 * @brief Register all TDX common functions with the function registry
 * @return true if all functions were registered successfully
 */
bool RegisterTdxCommonFunctions();

#endif // __TDX_COMMON_FUNC_H__