#include "KTCommonFunc.h"
#include "../utils/log.h"
#include <cstring>
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <cmath>

// KT Function ID offset for common functions
const int KT_COMMON_FUNCTION_ID_OFFSET = 2000;

// Static member initialization
std::unique_ptr<KTKbarManager> KTKbarManager::s_instance = nullptr;

// =============================================================================
// KTKbarData Implementation
// =============================================================================

KTKbarData::KTKbarData()
    : open(0.0f), high(0.0f), low(0.0f), close(0.0f), volume(0.0f), amount(0.0f), date(0), time(0)
{
}

KTKbarData::KTKbarData(float o, float h, float l, float c, float v, float a)
    : open(o), high(h), low(l), close(c), volume(v), amount(a), date(0), time(0)
{
}

void KTKbarData::SetDateTime(int d, int t)
{
    date = d;
    time = t;
}

void KTKbarData::ToSTKDATA(STKDATA& stkData) const
{
    stkData.date = date;
    stkData.time = time;
    stkData.open = open;
    stkData.high = high;
    stkData.low = low;
    stkData.close = close;
    stkData.volume = volume;
    stkData.amount = amount;
}

void KTKbarData::FromSTKDATA(const STKDATA& stkData)
{
    date = stkData.date;
    time = stkData.time;
    open = stkData.open;
    high = stkData.high;
    low = stkData.low;
    close = stkData.close;
    volume = stkData.volume;
    amount = stkData.amount;
}

// =============================================================================
// KTKbarKey Implementation
// =============================================================================

KTKbarKey::KTKbarKey(const std::string& sym, const std::string& per)
    : symbol(sym), period(per)
{
}

bool KTKbarKey::operator<(const KTKbarKey& other) const
{
    if (symbol != other.symbol) {
        return symbol < other.symbol;
    }
    return period < other.period;
}

// =============================================================================
// KTKbarManager Implementation
// =============================================================================

KTKbarManager::KTKbarManager()
{
    log_debug("KTKbarManager initialized");
}

KTKbarManager& KTKbarManager::GetInstance()
{
    if (!s_instance) {
        s_instance = std::unique_ptr<KTKbarManager>(new KTKbarManager());
    }
    return *s_instance;
}

void KTKbarManager::Cleanup()
{
    if (s_instance) {
        log_debug("KTKbarManager cleanup");
        s_instance.reset();
    }
}

void KTKbarManager::AddKbar(const std::string& symbol, const std::string& period, const KTKbarData& kbar)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    KTKbarKey key(symbol, period);
    m_kbarData[key].push_back(kbar);
}

const std::vector<KTKbarData>& KTKbarManager::GetKbarData(const std::string& symbol, const std::string& period) const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    KTKbarKey key(symbol, period);
    auto it = m_kbarData.find(key);
    if (it != m_kbarData.end()) {
        return it->second;
    }
    
    // Return empty vector if not found
    static const std::vector<KTKbarData> empty;
    return empty;
}

void KTKbarManager::SetKbarFromCALCINFO(const CALCINFO* pCalcInfo, const std::string& symbol, const std::string& period)
{
    if (!pCalcInfo || !pCalcInfo->pData || pCalcInfo->nCount <= 0) {
        log_error("Invalid CALCINFO data for SetKbarFromCALCINFO");
        return;
    }
    
    std::lock_guard<std::mutex> lock(m_mutex);
    KTKbarKey key(symbol, period);
    
    // Clear existing data
    m_kbarData[key].clear();
    m_kbarData[key].reserve(pCalcInfo->nCount);
    
    // Convert STKDATA to KTKbarData
    for (int i = 0; i < pCalcInfo->nCount; ++i) {
        KTKbarData kbar;
        kbar.FromSTKDATA(pCalcInfo->pData[i]);
        m_kbarData[key].push_back(kbar);
    }
    
    log_debug(("Loaded " + std::to_string(pCalcInfo->nCount) + " K-bars for " + symbol + "." + period).c_str());
}

void KTKbarManager::ClearKbarData(const std::string& symbol, const std::string& period)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    KTKbarKey key(symbol, period);
    m_kbarData.erase(key);
}

void KTKbarManager::ClearAllData()
{
    std::lock_guard<std::mutex> lock(m_mutex);
    m_kbarData.clear();
    log_debug("All K-bar data cleared");
}

int KTKbarManager::GetKbarCount(const std::string& symbol, const std::string& period) const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    KTKbarKey key(symbol, period);
    auto it = m_kbarData.find(key);
    return (it != m_kbarData.end()) ? static_cast<int>(it->second.size()) : 0;
}

void KTKbarManager::DebugLogAllData() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    log_debug(("KTKbarManager contains " + std::to_string(m_kbarData.size()) + " symbol/period combinations").c_str());
    
    for (const auto& pair : m_kbarData) {
        const auto& key = pair.first;
        const auto& data = pair.second;
        log_debug(("  " + key.symbol + "." + key.period + ": " + std::to_string(data.size()) + " K-bars").c_str());
    }
}

// =============================================================================
// KTSMAFunction Implementation
// =============================================================================

KTSMAFunction::KTSMAFunction()
    : KTFunctionBase(KT_COMMON_FUNCTION_ID_OFFSET + 1, "KT_SMA", "Simple Moving Average", "Technical Analysis", 1, false, 1)
{
}

pKTFUNC KTSMAFunction::GetKTFunctionPointer() const
{
    return KT_CalculateSMA;
}

BOOL KTSMAFunction::KT_CalculateSMA(CALCINFO* pCalcInfo)
{
    if (!KTFunctionBase::ValidateCALCINFOStatic(pCalcInfo, "KT_SMA")) {
        return FALSE;
    }
    
    // Get period parameter (default: 20)
    int period = static_cast<int>(KTTechnicalUtils::GetParameter(pCalcInfo, 0, 20.0f));
    if (period <= 0 || period > pCalcInfo->nCount) {
        log_error(("Invalid SMA period: " + std::to_string(period)).c_str());
        return FALSE;
    }
    
    // Extract close prices
    std::vector<float> closePrices(pCalcInfo->nCount);
    int extractedCount = KTTechnicalUtils::ExtractClosePrices(pCalcInfo, closePrices.data(), pCalcInfo->nCount);
    if (extractedCount != pCalcInfo->nCount) {
        log_error("Failed to extract close prices for SMA calculation");
        return FALSE;
    }
    
    // Calculate SMA
    if (!KTTechnicalUtils::CalculateSMA(closePrices.data(), period, pCalcInfo->ppResult[0], pCalcInfo->nCount)) {
        log_error("SMA calculation failed");
        return FALSE;
    }
    
    log_debug(("SMA(" + std::to_string(period) + ") calculated successfully for " + std::to_string(pCalcInfo->nCount) + " data points").c_str());
    return TRUE;
}

// =============================================================================
// KTEMAFunction Implementation
// =============================================================================

KTEMAFunction::KTEMAFunction()
    : KTFunctionBase(KT_COMMON_FUNCTION_ID_OFFSET + 2, "KT_EMA", "Exponential Moving Average", "Technical Analysis", 1, false, 1)
{
}

pKTFUNC KTEMAFunction::GetKTFunctionPointer() const
{
    return KT_CalculateEMA;
}

BOOL KTEMAFunction::KT_CalculateEMA(CALCINFO* pCalcInfo)
{
    if (!KTFunctionBase::ValidateCALCINFOStatic(pCalcInfo, "KT_EMA")) {
        return FALSE;
    }
    
    // Get period parameter (default: 20)
    int period = static_cast<int>(KTTechnicalUtils::GetParameter(pCalcInfo, 0, 20.0f));
    if (period <= 0 || period > pCalcInfo->nCount) {
        log_error(("Invalid EMA period: " + std::to_string(period)).c_str());
        return FALSE;
    }
    
    // Extract close prices
    std::vector<float> closePrices(pCalcInfo->nCount);
    int extractedCount = KTTechnicalUtils::ExtractClosePrices(pCalcInfo, closePrices.data(), pCalcInfo->nCount);
    if (extractedCount != pCalcInfo->nCount) {
        log_error("Failed to extract close prices for EMA calculation");
        return FALSE;
    }
    
    // Calculate EMA
    if (!KTTechnicalUtils::CalculateEMA(closePrices.data(), period, pCalcInfo->ppResult[0], pCalcInfo->nCount)) {
        log_error("EMA calculation failed");
        return FALSE;
    }
    
    log_debug(("EMA(" + std::to_string(period) + ") calculated successfully for " + std::to_string(pCalcInfo->nCount) + " data points").c_str());
    return TRUE;
}

// =============================================================================
// KTMACDFunction Implementation
// =============================================================================

KTMACDFunction::KTMACDFunction()
    : KTFunctionBase(KT_COMMON_FUNCTION_ID_OFFSET + 3, "KT_MACD", "MACD Indicator", "Technical Analysis", 1, false, 3)
{
}

pKTFUNC KTMACDFunction::GetKTFunctionPointer() const
{
    return KT_CalculateMACD;
}

BOOL KTMACDFunction::KT_CalculateMACD(CALCINFO* pCalcInfo)
{
    if (!KTFunctionBase::ValidateCALCINFOStatic(pCalcInfo, "KT_MACD")) {
        return FALSE;
    }
    
    if (pCalcInfo->nResultCount < 3) {
        log_error("MACD requires at least 3 result arrays (MACD, Signal, Histogram)");
        return FALSE;
    }
    
    // Get parameters (defaults: 12, 26, 9)
    int fastPeriod = static_cast<int>(KTTechnicalUtils::GetParameter(pCalcInfo, 0, 12.0f));
    int slowPeriod = static_cast<int>(KTTechnicalUtils::GetParameter(pCalcInfo, 1, 26.0f));
    int signalPeriod = static_cast<int>(KTTechnicalUtils::GetParameter(pCalcInfo, 2, 9.0f));
    
    if (fastPeriod <= 0 || slowPeriod <= 0 || signalPeriod <= 0 || slowPeriod <= fastPeriod) {
        log_error("Invalid MACD parameters");
        return FALSE;
    }
    
    // Extract close prices
    std::vector<float> closePrices(pCalcInfo->nCount);
    int extractedCount = KTTechnicalUtils::ExtractClosePrices(pCalcInfo, closePrices.data(), pCalcInfo->nCount);
    if (extractedCount != pCalcInfo->nCount) {
        log_error("Failed to extract close prices for MACD calculation");
        return FALSE;
    }
    
    // Calculate MACD
    if (!KTTechnicalUtils::CalculateMACD(closePrices.data(), fastPeriod, slowPeriod, signalPeriod,
                                         pCalcInfo->ppResult[0], pCalcInfo->ppResult[1], pCalcInfo->ppResult[2], pCalcInfo->nCount)) {
        log_error("MACD calculation failed");
        return FALSE;
    }
    
    log_debug(("MACD(" + std::to_string(fastPeriod) + "," + std::to_string(slowPeriod) + "," + std::to_string(signalPeriod) + ") calculated successfully").c_str());
    return TRUE;
}

// =============================================================================
// KTRSIFunction Implementation
// =============================================================================

KTRSIFunction::KTRSIFunction()
    : KTFunctionBase(KT_COMMON_FUNCTION_ID_OFFSET + 4, "KT_RSI", "Relative Strength Index", "Technical Analysis", 1, false, 1)
{
}

pKTFUNC KTRSIFunction::GetKTFunctionPointer() const
{
    return KT_CalculateRSI;
}

BOOL KTRSIFunction::KT_CalculateRSI(CALCINFO* pCalcInfo)
{
    if (!KTFunctionBase::ValidateCALCINFOStatic(pCalcInfo, "KT_RSI")) {
        return FALSE;
    }
    
    // Get period parameter (default: 14)
    int period = static_cast<int>(KTTechnicalUtils::GetParameter(pCalcInfo, 0, 14.0f));
    if (period <= 0 || period > pCalcInfo->nCount) {
        log_error(("Invalid RSI period: " + std::to_string(period)).c_str());
        return FALSE;
    }
    
    // Extract close prices
    std::vector<float> closePrices(pCalcInfo->nCount);
    int extractedCount = KTTechnicalUtils::ExtractClosePrices(pCalcInfo, closePrices.data(), pCalcInfo->nCount);
    if (extractedCount != pCalcInfo->nCount) {
        log_error("Failed to extract close prices for RSI calculation");
        return FALSE;
    }
    
    // Calculate RSI
    if (!KTTechnicalUtils::CalculateRSI(closePrices.data(), period, pCalcInfo->ppResult[0], pCalcInfo->nCount)) {
        log_error("RSI calculation failed");
        return FALSE;
    }
    
    log_debug(("RSI(" + std::to_string(period) + ") calculated successfully for " + std::to_string(pCalcInfo->nCount) + " data points").c_str());
    return TRUE;
}

// =============================================================================
// KTTechnicalUtils Implementation
// =============================================================================

namespace KTTechnicalUtils
{
    bool CalculateSMA(const float* data, int period, float* output, int count)
    {
        if (!data || !output || period <= 0 || count <= 0) {
            return false;
        }
        
        // Initialize output with NaN for insufficient data
        for (int i = 0; i < period - 1; ++i) {
            output[i] = std::numeric_limits<float>::quiet_NaN();
        }
        
        // Calculate SMA
        for (int i = period - 1; i < count; ++i) {
            float sum = 0.0f;
            for (int j = 0; j < period; ++j) {
                sum += data[i - j];
            }
            output[i] = sum / period;
        }
        
        return true;
    }
    
    bool CalculateEMA(const float* data, int period, float* output, int count)
    {
        if (!data || !output || period <= 0 || count <= 0) {
            return false;
        }
        
        float multiplier = 2.0f / (period + 1.0f);
        
        // Initialize first value
        output[0] = data[0];
        
        // Calculate EMA
        for (int i = 1; i < count; ++i) {
            output[i] = (data[i] * multiplier) + (output[i - 1] * (1.0f - multiplier));
        }
        
        return true;
    }
    
    bool CalculateMACD(const float* data, int fastPeriod, int slowPeriod, int signalPeriod,
                       float* macdLine, float* signalLine, float* histogram, int count)
    {
        if (!data || !macdLine || !signalLine || !histogram || count <= 0) {
            return false;
        }
        
        // Calculate fast and slow EMAs
        std::vector<float> fastEMA(count);
        std::vector<float> slowEMA(count);
        
        if (!CalculateEMA(data, fastPeriod, fastEMA.data(), count) ||
            !CalculateEMA(data, slowPeriod, slowEMA.data(), count)) {
            return false;
        }
        
        // Calculate MACD line (fast EMA - slow EMA)
        for (int i = 0; i < count; ++i) {
            macdLine[i] = fastEMA[i] - slowEMA[i];
        }
        
        // Calculate signal line (EMA of MACD line)
        if (!CalculateEMA(macdLine, signalPeriod, signalLine, count)) {
            return false;
        }
        
        // Calculate histogram (MACD - Signal)
        for (int i = 0; i < count; ++i) {
            histogram[i] = macdLine[i] - signalLine[i];
        }
        
        return true;
    }
    
    bool CalculateRSI(const float* data, int period, float* output, int count)
    {
        if (!data || !output || period <= 0 || count <= period) {
            return false;
        }
        
        // Initialize output with NaN for insufficient data
        for (int i = 0; i < period; ++i) {
            output[i] = std::numeric_limits<float>::quiet_NaN();
        }
        
        // Calculate initial average gain and loss
        float avgGain = 0.0f;
        float avgLoss = 0.0f;
        
        for (int i = 1; i <= period; ++i) {
            float change = data[i] - data[i - 1];
            if (change > 0) {
                avgGain += change;
            } else {
                avgLoss += (-change);
            }
        }
        
        avgGain /= period;
        avgLoss /= period;
        
        // Calculate RSI for the first valid point
        if (avgLoss != 0.0f) {
            float rs = avgGain / avgLoss;
            output[period] = 100.0f - (100.0f / (1.0f + rs));
        } else {
            output[period] = 100.0f;
        }
        
        // Calculate RSI for remaining points using smoothed averages
        for (int i = period + 1; i < count; ++i) {
            float change = data[i] - data[i - 1];
            float gain = (change > 0) ? change : 0.0f;
            float loss = (change < 0) ? (-change) : 0.0f;
            
            avgGain = ((avgGain * (period - 1)) + gain) / period;
            avgLoss = ((avgLoss * (period - 1)) + loss) / period;
            
            if (avgLoss != 0.0f) {
                float rs = avgGain / avgLoss;
                output[i] = 100.0f - (100.0f / (1.0f + rs));
            } else {
                output[i] = 100.0f;
            }
        }
        
        return true;
    }
    
    int ExtractClosePrices(const CALCINFO* pCalcInfo, float* output, int maxCount)
    {
        if (!pCalcInfo || !pCalcInfo->pData || !output || maxCount <= 0) {
            return 0;
        }
        
        int count = std::min(pCalcInfo->nCount, maxCount);
        for (int i = 0; i < count; ++i) {
            output[i] = pCalcInfo->pData[i].close;
        }
        
        return count;
    }
    
    float GetParameter(const CALCINFO* pCalcInfo, int paramIndex, float defaultValue)
    {
        if (!pCalcInfo || !pCalcInfo->pParam || !pCalcInfo->pParam->pParam ||
            paramIndex < 0 || paramIndex >= pCalcInfo->pParam->nParamCount) {
            return defaultValue;
        }
        
        return pCalcInfo->pParam->pParam[paramIndex];
    }
}

// =============================================================================
// Registration Function
// =============================================================================

bool RegisterKTCommonFunctions()
{
    auto& registry = KTFunctionRegistry::GetInstance();
    bool success = true;
    
    try {
        // Register SMA function
        auto smaFunc = std::make_shared<KTSMAFunction>();
        if (!registry.RegisterFunction(smaFunc)) {
            log_error("Failed to register KT_SMA function");
            success = false;
        }
        
        // Register EMA function
        auto emaFunc = std::make_shared<KTEMAFunction>();
        if (!registry.RegisterFunction(emaFunc)) {
            log_error("Failed to register KT_EMA function");
            success = false;
        }
        
        // Register MACD function
        auto macdFunc = std::make_shared<KTMACDFunction>();
        if (!registry.RegisterFunction(macdFunc)) {
            log_error("Failed to register KT_MACD function");
            success = false;
        }
        
        // Register RSI function
        auto rsiFunc = std::make_shared<KTRSIFunction>();
        if (!registry.RegisterFunction(rsiFunc)) {
            log_error("Failed to register KT_RSI function");
            success = false;
        }
        
        if (success) {
            log_info("All KT common functions registered successfully");
        }
    }
    catch (const std::exception& e) {
        log_error(("Exception during KT common function registration: " + std::string(e.what())).c_str());
        success = false;
    }
    
    return success;
}