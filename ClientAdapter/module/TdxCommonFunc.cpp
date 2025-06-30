#include "TdxCommonFunc.h"
#include "../utils/log.h"
#include <cstring>
#include <algorithm>
#include <sstream>
#include <iomanip>

// TDX Function ID offset
constexpr int TDX_FUNCTION_ID_OFFSET = 1;

// Static member initialization
std::unique_ptr<KbarManager> KbarManager::s_instance = nullptr;

// Temporary storage for building Kbar data during TDX API calls
static std::vector<float> temp_open, temp_high, temp_low, temp_close;
static std::vector<long> temp_volume;
static std::vector<short> temp_year;
static std::vector<char> temp_month, temp_day, temp_hour, temp_minute;
static std::string current_symbol = "DEFAULT";
static std::string current_period = "1min";

/**
 * @brief Default constructor for KbarData
 */
KbarData::KbarData()
    : open(0.0f), high(0.0f), low(0.0f), close(0.0f), volume(0)
    , year(0), month(0), day(0), hour(0), minute(0)
{
}

/**
 * @brief Constructor with OHLCV data for KbarData
 * @param o Open price
 * @param h High price
 * @param l Low price
 * @param c Close price
 * @param v Volume
 */
KbarData::KbarData(float o, float h, float l, float c, long v)
    : open(o), high(h), low(l), close(c), volume(v)
    , year(0), month(0), day(0), hour(0), minute(0)
{
}

/**
 * @brief Set date information for KbarData
 * @param y Year
 * @param m Month
 * @param d Day
 */
void KbarData::SetDate(short y, char m, char d)
{
    year = y;
    month = m;
    day = d;
}

/**
 * @brief Set time information for KbarData
 * @param h Hour
 * @param min Minute
 */
void KbarData::SetTime(char h, char min)
{
    hour = h;
    minute = min;
}

/**
 * @brief Constructor for KbarKey
 * @param sym Symbol name
 * @param per Period string
 */
KbarKey::KbarKey(const std::string& sym, const std::string& per)
    : symbol(sym), period(per)
{
}

/**
 * @brief Less-than operator for KbarKey map ordering
 * @param other Other KbarKey to compare
 * @return true if this key is less than other
 */
bool KbarKey::operator<(const KbarKey& other) const
{
    if (symbol != other.symbol)
        return symbol < other.symbol;
    return period < other.period;
}

/**
 * @brief Private constructor for KbarManager singleton
 */
KbarManager::KbarManager()
{
}

/**
 * @brief Get singleton instance of KbarManager
 * @return Reference to the singleton KbarManager instance
 */
KbarManager& KbarManager::GetInstance()
{
    if (!s_instance)
    {
        s_instance.reset(new KbarManager());
    }
    return *s_instance;
}

/**
 * @brief Add Kbar data for a specific symbol and period
 * @param symbol Symbol name
 * @param period Period string
 * @param kbar Kbar data to add
 */
void KbarManager::AddKbar(const std::string& symbol, const std::string& period, const KbarData& kbar)
{
    KbarKey key(symbol, period);
    m_kbarData[key].push_back(kbar);
}

/**
 * @brief Get Kbar data for a specific symbol and period
 * @param symbol Symbol name
 * @param period Period string
 * @return Const reference to vector of Kbar data
 */
const std::vector<KbarData>& KbarManager::GetKbarData(const std::string& symbol, const std::string& period) const
{
    KbarKey key(symbol, period);
    auto it = m_kbarData.find(key);
    if (it != m_kbarData.end())
    {
        return it->second;
    }
    
    static std::vector<KbarData> empty_vector;
    return empty_vector;
}

/**
 * @brief Clear all Kbar data for a specific symbol and period
 * @param symbol Symbol name
 * @param period Period string
 */
void KbarManager::ClearKbarData(const std::string& symbol, const std::string& period)
{
    KbarKey key(symbol, period);
    auto it = m_kbarData.find(key);
    if (it != m_kbarData.end())
    {
        it->second.clear();
    }
}

/**
 * @brief Clear all Kbar data
 */
void KbarManager::ClearAllData()
{
    m_kbarData.clear();
}

/**
 * @brief Get number of Kbar records for a specific symbol and period
 * @param symbol Symbol name
 * @param period Period string
 * @return Number of Kbar records
 */
int KbarManager::GetKbarCount(const std::string& symbol, const std::string& period) const
{
    KbarKey key(symbol, period);
    auto it = m_kbarData.find(key);
    if (it != m_kbarData.end())
    {
        return static_cast<int>(it->second.size());
    }
    return 0;
}

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
void KbarManager::SetKbarArrays(const std::string& symbol, const std::string& period, int count,
                               const float* openArray, const float* highArray, const float* lowArray,
                               const float* closeArray, const long* volumeArray,
                               const short* yearArray, const char* monthArray, const char* dayArray,
                               const char* hourArray, const char* minuteArray)
{
    KbarKey key(symbol, period);
    m_kbarData[key].clear();
    m_kbarData[key].reserve(count);
    
    for (int i = 0; i < count; i++)
    {
        KbarData kbar(openArray[i], highArray[i], lowArray[i], closeArray[i], volumeArray[i]);
        kbar.SetDate(yearArray[i], monthArray[i], dayArray[i]);
        kbar.SetTime(hourArray[i], minuteArray[i]);
        m_kbarData[key].push_back(kbar);
    }
}

/**
 * @brief Helper function to encode symbol and period into float for TDX compatibility
 * @param symbol Symbol string
 * @param period Period string
 * @return Encoded float value
 */
float EncodeSymbolPeriod(const std::string& symbol, const std::string& period)
{
    // Simple hash-based encoding for TDX compatibility
    // This is a basic implementation - can be enhanced for better collision avoidance
    std::hash<std::string> hasher;
    size_t hash1 = hasher(symbol);
    size_t hash2 = hasher(period);
    
    // Combine hashes and convert to float (keeping it within reasonable range)
    float encoded = static_cast<float>((hash1 ^ (hash2 << 1)) % 1000000);
    return encoded;
}

/**
 * @brief Helper function to decode symbol and period from float
 * @param encoded Encoded float value
 * @param symbol Output symbol string
 * @param period Output period string
 */
void DecodeSymbolPeriod(float encoded, std::string& symbol, std::string& period)
{
    // The encoded value format is: Symbol*100 + Period
    // TDX Period function results from 0 to 13, representing 1/5/15/30/60 minutes, daily/weekly/monthly, multi-minute, multi-day/quarterly/yearly, 5-second/multi-second lines, 13+ for custom periods
    // Example: 600001.SH 1min -> 600001*100 + 1 = 600001001
    int encodedInt = static_cast<int>(encoded);
    symbol = std::to_string(encodedInt / 100);
    period = std::to_string(encodedInt % 100);

    log_debug("Decoded symbol: %s, period: %s", symbol.c_str(), period.c_str());
}

/**
 * @brief TDX API function to set OHLC data for Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (not used in this function)
 * @param pfINa Input array A (Open prices)
 * @param pfINb Input array B (High prices) 
 * @param pfINc Input array C (Low prices)
 */
TDX_EXPORT(TdxKbar_SetOHLC)
{
    temp_open.clear();
    temp_high.clear();
    temp_low.clear();
    
    temp_open.reserve(DataLen);
    temp_high.reserve(DataLen);
    temp_low.reserve(DataLen);
    
    for (int i = 0; i < DataLen; i++)
    {
        temp_open.push_back(pfINa[i]);
        temp_high.push_back(pfINb[i]);
        temp_low.push_back(pfINc[i]);
    }
}

/**
 * @brief TDX API function to set Close and Volume data for Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (not used in this function)
 * @param pfINa Input array A (Close prices)
 * @param pfINb Input array B (Volume data)
 * @param pfINc Input array C (not used)
 */
TDX_EXPORT(TdxKbar_SetCloseVolume)
{
    temp_close.clear();
    temp_volume.clear();
    
    temp_close.reserve(DataLen);
    temp_volume.reserve(DataLen);
    
    for (int i = 0; i < DataLen; i++)
    {
        temp_close.push_back(pfINa[i]);
        temp_volume.push_back(static_cast<long>(pfINb[i]));
    }
}

/**
 * @brief TDX API function to set date information for Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (not used in this function)
 * @param pfINa Input array A (Year)
 * @param pfINb Input array B (Month)
 * @param pfINc Input array C (Day)
 */
TDX_EXPORT(TdxKbar_SetDate)
{
    temp_year.clear();
    temp_month.clear();
    temp_day.clear();
    
    temp_year.reserve(DataLen);
    temp_month.reserve(DataLen);
    temp_day.reserve(DataLen);
    
    for (int i = 0; i < DataLen; i++)
    {
        temp_year.push_back(static_cast<short>(pfINa[i]));
        temp_month.push_back(static_cast<char>(pfINb[i]));
        temp_day.push_back(static_cast<char>(pfINc[i]));
    }
}

/**
 * @brief TDX API function to set time information for Kbar and finalize data
 * @param DataLen Number of data points
 * @param pfOUT Output array (not used in this function)
 * @param pfINa Input array A (Hour)
 * @param pfINb Input array B (Minute)
 * @param pfINc Input array C (Symbol and period encoded as float)
 */
TDX_EXPORT(TdxKbar_SetTimeAndFinalize)
{
    temp_hour.clear();
    temp_minute.clear();
    
    temp_hour.reserve(DataLen);
    temp_minute.reserve(DataLen);
    
    for (int i = 0; i < DataLen; i++)
    {
        temp_hour.push_back(static_cast<char>(pfINa[i]));
        temp_minute.push_back(static_cast<char>(pfINb[i]));
    }
    
    // Extract symbol and period from encoded value (use first element)
    if (DataLen > 0)
    {
        DecodeSymbolPeriod(pfINc[0], current_symbol, current_period);
    }
    
    // Now finalize and store all the Kbar data
    KbarManager& manager = KbarManager::GetInstance();
    manager.ClearKbarData(current_symbol, current_period);
    
    int minSize = std::min({static_cast<int>(temp_open.size()), 
                           static_cast<int>(temp_high.size()),
                           static_cast<int>(temp_low.size()),
                           static_cast<int>(temp_close.size()),
                           static_cast<int>(temp_volume.size()),
                           static_cast<int>(temp_year.size()),
                           static_cast<int>(temp_month.size()),
                           static_cast<int>(temp_day.size()),
                           static_cast<int>(temp_hour.size()),
                           static_cast<int>(temp_minute.size())});
    
    for (int i = 0; i < minSize; i++)
    {
        KbarData kbar(temp_open[i], temp_high[i], temp_low[i], temp_close[i], temp_volume[i]);
        kbar.SetDate(temp_year[i], temp_month[i], temp_day[i]);
        kbar.SetTime(temp_hour[i], temp_minute[i]);
        manager.AddKbar(current_symbol, current_period, kbar);
    }
    
    // Clear temporary storage
    temp_open.clear();
    temp_high.clear();
    temp_low.clear();
    temp_close.clear();
    temp_volume.clear();
    temp_year.clear();
    temp_month.clear();
    temp_day.clear();
    temp_hour.clear();
    temp_minute.clear();
}

/**
 * @brief TDX API function to get OHLC data from Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (OHLC data encoded)
 * @param pfINa Input array A (Symbol and period encoded)
 * @param pfINb Input array B (Data type: 0=Open, 1=High, 2=Low, 3=Close)
 * @param pfINc Input array C (Index offset)
 */
TDX_EXPORT(TdxKbar_GetOHLC)
{
    if (DataLen <= 0) return;
    
    std::string symbol, period;
    DecodeSymbolPeriod(pfINa[0], symbol, period);
    
    int dataType = static_cast<int>(pfINb[0]); // 0=Open, 1=High, 2=Low, 3=Close
    int indexOffset = static_cast<int>(pfINc[0]);
    
    KbarManager& manager = KbarManager::GetInstance();
    const std::vector<KbarData>& kbarData = manager.GetKbarData(symbol, period);
    
    for (int i = 0; i < DataLen; i++)
    {
        int dataIndex = i + indexOffset;
        if (dataIndex >= 0 && dataIndex < static_cast<int>(kbarData.size()))
        {
            switch (dataType)
            {
                case 0: pfOUT[i] = kbarData[dataIndex].open; break;
                case 1: pfOUT[i] = kbarData[dataIndex].high; break;
                case 2: pfOUT[i] = kbarData[dataIndex].low; break;
                case 3: pfOUT[i] = kbarData[dataIndex].close; break;
                default: pfOUT[i] = 0.0f; break;
            }
        }
        else
        {
            pfOUT[i] = 0.0f;
        }
    }
}

/**
 * @brief TDX API function to get Volume data from Kbar
 * @param DataLen Number of data points
 * @param pfOUT Output array (Volume data)
 * @param pfINa Input array A (Symbol and period encoded)
 * @param pfINb Input array B (not used)
 * @param pfINc Input array C (Index offset)
 */
TDX_EXPORT(TdxKbar_GetVolume)
{
    if (DataLen <= 0) return;
    
    std::string symbol, period;
    DecodeSymbolPeriod(pfINa[0], symbol, period);
    
    int indexOffset = static_cast<int>(pfINc[0]);
    
    KbarManager& manager = KbarManager::GetInstance();
    const std::vector<KbarData>& kbarData = manager.GetKbarData(symbol, period);
    
    for (int i = 0; i < DataLen; i++)
    {
        int dataIndex = i + indexOffset;
        if (dataIndex >= 0 && dataIndex < static_cast<int>(kbarData.size()))
        {
            pfOUT[i] = static_cast<float>(kbarData[dataIndex].volume);
        }
        else
        {
            pfOUT[i] = 0.0f;
        }
    }
}

// ============================================================================
// TDX Function Wrapper Classes
// ============================================================================

/**
 * @brief Wrapper class for TdxKbar_SetOHLC function
 */
class TdxKbarSetOHLCFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxKbarSetOHLCFunction()
        : TdxFunctionBase(TDX_FUNCTION_ID_OFFSET + 0, "TdxKbar_SetOHLC", "Set OHLC data for Kbar", "Kbar", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxKbar_SetOHLC
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxKbar_SetOHLC;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Open prices, pInB=High prices, pInC=Low prices, pOut=result";
    }
};

/**
 * @brief Wrapper class for TdxKbar_SetCloseVolume function
 */
class TdxKbarSetCloseVolumeFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxKbarSetCloseVolumeFunction()
        : TdxFunctionBase(TDX_FUNCTION_ID_OFFSET + 1, "TdxKbar_SetCloseVolume", "Set Close and Volume data for Kbar", "Kbar", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxKbar_SetCloseVolume
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxKbar_SetCloseVolume;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Close prices, pInB=Volume data, pInC=unused, pOut=result";
    }
};

/**
 * @brief Wrapper class for TdxKbar_SetDate function
 */
class TdxKbarSetDateFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxKbarSetDateFunction()
        : TdxFunctionBase(TDX_FUNCTION_ID_OFFSET + 2, "TdxKbar_SetDate", "Set date information for Kbar", "Kbar", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxKbar_SetDate
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxKbar_SetDate;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Year, pInB=Month, pInC=Day, pOut=result";
    }
};

/**
 * @brief Wrapper class for TdxKbar_SetTimeAndFinalize function
 */
class TdxKbarSetTimeAndFinalizeFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxKbarSetTimeAndFinalizeFunction()
        : TdxFunctionBase(TDX_FUNCTION_ID_OFFSET + 3, "TdxKbar_SetTimeAndFinalize", "Set time information and finalize Kbar data", "Kbar", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxKbar_SetTimeAndFinalize
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxKbar_SetTimeAndFinalize;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Hour, pInB=Minute, pInC=Symbol and period encoded, pOut=result";
    }
};

/**
 * @brief Wrapper class for TdxKbar_GetOHLC function
 */
class TdxKbarGetOHLCFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxKbarGetOHLCFunction()
        : TdxFunctionBase(TDX_FUNCTION_ID_OFFSET + 4, "TdxKbar_GetOHLC", "Get OHLC data from Kbar", "Kbar", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxKbar_GetOHLC
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxKbar_GetOHLC;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Symbol and period encoded, pInB=Data type (0=Open,1=High,2=Low,3=Close), pInC=Index offset, pOut=OHLC data";
    }
};

/**
 * @brief Wrapper class for TdxKbar_GetVolume function
 */
class TdxKbarGetVolumeFunction : public TdxFunctionBase
{
public:
    /**
     * @brief Constructor
     */
    TdxKbarGetVolumeFunction()
        : TdxFunctionBase(TDX_FUNCTION_ID_OFFSET + 5, "TdxKbar_GetVolume", "Get Volume data from Kbar", "Kbar", 1, false)
    {
    }

    /**
     * @brief Get unique C-style function pointer
     * @return Function pointer for TdxKbar_GetVolume
     */
    pPluginFUNC GetCFunctionPointer() override
    {
        return &TdxKbar_GetVolume;
    }

    /**
     * @brief Provide detailed parameter information
     * @return Parameter usage description
     */
    std::string GetParameterInfo() const override
    {
        return "Parameters: pInA=Symbol and period encoded, pInB=Index offset, pInC=unused, pOut=Volume data";
    }
};

// ============================================================================
// Function Registration
// ============================================================================

/**
 * @brief Register all TDX common functions with the function registry
 * @return true if all functions were registered successfully
 */
bool RegisterTdxCommonFunctions()
{
    try
    {
        auto& registry = TdxFunctionRegistry::GetInstance();
        bool success = true;
        
        // Register all Kbar functions
        success &= registry.RegisterFunction(std::make_shared<TdxKbarSetOHLCFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxKbarSetCloseVolumeFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxKbarSetDateFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxKbarSetTimeAndFinalizeFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxKbarGetOHLCFunction>());
        success &= registry.RegisterFunction(std::make_shared<TdxKbarGetVolumeFunction>());
        
        if (success)
        {
            // Log success if logging is available
            log_debug("All TDX common functions registered successfully");
        }
        else
        {
            // Log failure if logging is available
            log_error("Some TDX common functions failed to register");
        }
        
        return success;
    }
    catch (const std::exception& e)
    {
        // Log exception if logging is available
        log_error("Exception while registering TDX common functions: %s", e.what());
        return false;
    }
    catch (...)
    {
        // Log unknown exception if logging is available
        log_error("Unknown exception while registering TDX common functions");
        return false;
    }
}

