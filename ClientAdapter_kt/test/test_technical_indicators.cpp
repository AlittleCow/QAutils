#include "../core/KTPluginMain.h"
#include "../core/KTFunctionRegistry.h"
#include "../module/KTCommonFunc.h"
#include "../utils/log.h"
#include <iostream>
#include <vector>
#include <iomanip>
#include <cmath>

// Test data generator
std::vector<STKDATA> GenerateTestData(int count)
{
    std::vector<STKDATA> data(count);
    
    // Generate sample price data with some trend and volatility
    float basePrice = 100.0f;
    for (int i = 0; i < count; ++i) {
        float trend = i * 0.1f; // Slight upward trend
        float noise = sin(i * 0.3f) * 2.0f; // Some volatility
        float price = basePrice + trend + noise;
        
        data[i].date = 20240101 + i;
        data[i].time = 93000 + (i * 100); // 9:30:00, 9:31:00, etc.
        data[i].open = price - 0.5f;
        data[i].high = price + 1.0f;
        data[i].low = price - 1.0f;
        data[i].close = price;
        data[i].volume = 1000.0f + (i * 10.0f);
        data[i].amount = data[i].volume * price;
    }
    
    return data;
}

// Helper function to create CALCINFO
CALCINFO CreateCALCINFO(const std::vector<STKDATA>& data, int resultCount, const std::vector<float>& params = {})
{
    CALCINFO calcInfo = {};
    
    // Basic info
    calcInfo.nCount = static_cast<int>(data.size());
    calcInfo.pData = const_cast<STKDATA*>(data.data());
    calcInfo.nType = DTYPE_DAY;
    strcpy_s(calcInfo.szLabel, sizeof(calcInfo.szLabel), "TEST001");
    
    // Result arrays
    calcInfo.nResultCount = resultCount;
    static std::vector<std::vector<float>> resultArrays;
    static std::vector<float*> resultPointers;
    
    resultArrays.clear();
    resultPointers.clear();
    
    for (int i = 0; i < resultCount; ++i) {
        resultArrays.emplace_back(data.size(), 0.0f);
        resultPointers.push_back(resultArrays.back().data());
    }
    
    calcInfo.ppResult = resultPointers.data();
    
    // Parameters
    static CALCPARAM calcParam = {};
    static std::vector<float> paramArray;
    
    if (!params.empty()) {
        paramArray = params;
        calcParam.nParamCount = static_cast<int>(params.size());
        calcParam.pParam = paramArray.data();
        calcInfo.pParam = &calcParam;
    } else {
        calcInfo.pParam = nullptr;
    }
    
    return calcInfo;
}

// Test SMA function
bool TestSMA()
{
    std::cout << "\n=== Testing SMA (Simple Moving Average) ===\n";
    
    auto data = GenerateTestData(50);
    auto calcInfo = CreateCALCINFO(data, 1, {20.0f}); // 20-period SMA
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(2001); // KT_SMA function ID
    
    if (!function) {
        std::cout << "ERROR: KT_SMA function not found!\n";
        return false;
    }
    
    auto ktFunc = function->GetKTFunctionPointer();
    if (!ktFunc) {
        std::cout << "ERROR: KT_SMA function pointer is null!\n";
        return false;
    }
    
    BOOL result = ktFunc(&calcInfo);
    if (!result) {
        std::cout << "ERROR: SMA calculation failed!\n";
        return false;
    }
    
    // Display results
    std::cout << "SMA(20) Results (last 10 values):\n";
    for (int i = calcInfo.nCount - 10; i < calcInfo.nCount; ++i) {
        if (!std::isnan(calcInfo.ppResult[0][i])) {
            std::cout << "  Day " << std::setw(2) << i + 1 << ": " 
                      << std::fixed << std::setprecision(2) << calcInfo.ppResult[0][i] << "\n";
        }
    }
    
    std::cout << "SMA test PASSED\n";
    return true;
}

// Test EMA function
bool TestEMA()
{
    std::cout << "\n=== Testing EMA (Exponential Moving Average) ===\n";
    
    auto data = GenerateTestData(50);
    auto calcInfo = CreateCALCINFO(data, 1, {20.0f}); // 20-period EMA
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(2002); // KT_EMA function ID
    
    if (!function) {
        std::cout << "ERROR: KT_EMA function not found!\n";
        return false;
    }
    
    auto ktFunc = function->GetKTFunctionPointer();
    BOOL result = ktFunc(&calcInfo);
    if (!result) {
        std::cout << "ERROR: EMA calculation failed!\n";
        return false;
    }
    
    // Display results
    std::cout << "EMA(20) Results (last 10 values):\n";
    for (int i = calcInfo.nCount - 10; i < calcInfo.nCount; ++i) {
        std::cout << "  Day " << std::setw(2) << i + 1 << ": " 
                  << std::fixed << std::setprecision(2) << calcInfo.ppResult[0][i] << "\n";
    }
    
    std::cout << "EMA test PASSED\n";
    return true;
}

// Test MACD function
bool TestMACD()
{
    std::cout << "\n=== Testing MACD Indicator ===\n";
    
    auto data = GenerateTestData(100);
    auto calcInfo = CreateCALCINFO(data, 3, {12.0f, 26.0f, 9.0f}); // MACD(12,26,9)
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(2003); // KT_MACD function ID
    
    if (!function) {
        std::cout << "ERROR: KT_MACD function not found!\n";
        return false;
    }
    
    auto ktFunc = function->GetKTFunctionPointer();
    BOOL result = ktFunc(&calcInfo);
    if (!result) {
        std::cout << "ERROR: MACD calculation failed!\n";
        return false;
    }
    
    // Display results
    std::cout << "MACD(12,26,9) Results (last 5 values):\n";
    std::cout << "  Day    MACD     Signal   Histogram\n";
    for (int i = calcInfo.nCount - 5; i < calcInfo.nCount; ++i) {
        std::cout << "  " << std::setw(3) << i + 1 << ": "
                  << std::fixed << std::setprecision(3) 
                  << std::setw(8) << calcInfo.ppResult[0][i] << " "
                  << std::setw(8) << calcInfo.ppResult[1][i] << " "
                  << std::setw(8) << calcInfo.ppResult[2][i] << "\n";
    }
    
    std::cout << "MACD test PASSED\n";
    return true;
}

// Test RSI function
bool TestRSI()
{
    std::cout << "\n=== Testing RSI (Relative Strength Index) ===\n";
    
    auto data = GenerateTestData(50);
    auto calcInfo = CreateCALCINFO(data, 1, {14.0f}); // 14-period RSI
    
    auto& registry = KTFunctionRegistry::GetInstance();
    auto function = registry.GetFunction(2004); // KT_RSI function ID
    
    if (!function) {
        std::cout << "ERROR: KT_RSI function not found!\n";
        return false;
    }
    
    auto ktFunc = function->GetKTFunctionPointer();
    BOOL result = ktFunc(&calcInfo);
    if (!result) {
        std::cout << "ERROR: RSI calculation failed!\n";
        return false;
    }
    
    // Display results
    std::cout << "RSI(14) Results (last 10 values):\n";
    for (int i = calcInfo.nCount - 10; i < calcInfo.nCount; ++i) {
        if (!std::isnan(calcInfo.ppResult[0][i])) {
            std::cout << "  Day " << std::setw(2) << i + 1 << ": " 
                      << std::fixed << std::setprecision(2) << calcInfo.ppResult[0][i] << "\n";
        }
    }
    
    std::cout << "RSI test PASSED\n";
    return true;
}

// Test KTKbarManager
bool TestKbarManager()
{
    std::cout << "\n=== Testing KTKbarManager ===\n";
    
    auto& manager = KTKbarManager::GetInstance();
    
    // Clear any existing data
    manager.ClearAllData();
    
    // Add some test data
    KTKbarData kbar1(100.0f, 102.0f, 99.0f, 101.0f, 1000.0f, 101000.0f);
    kbar1.SetDateTime(20240101, 93000);
    
    KTKbarData kbar2(101.0f, 103.0f, 100.0f, 102.0f, 1100.0f, 112200.0f);
    kbar2.SetDateTime(20240102, 93000);
    
    manager.AddKbar("TEST001", "1D", kbar1);
    manager.AddKbar("TEST001", "1D", kbar2);
    
    // Test retrieval
    const auto& data = manager.GetKbarData("TEST001", "1D");
    if (data.size() != 2) {
        std::cout << "ERROR: Expected 2 K-bars, got " << data.size() << "\n";
        return false;
    }
    
    // Test count
    int count = manager.GetKbarCount("TEST001", "1D");
    if (count != 2) {
        std::cout << "ERROR: Expected count 2, got " << count << "\n";
        return false;
    }
    
    // Test debug output
    manager.DebugLogAllData();
    
    std::cout << "KTKbarManager test PASSED\n";
    return true;
}

int main()
{
    std::cout << "=== KT Technical Indicators Test Suite ===\n";
    
    // Initialize logging
    log_init();
    
    // Initialize plugin
    if (!KTPluginManager::Initialize()) {
        std::cerr << "Failed to initialize KT plugin\n";
        return 1;
    }
    
    bool allTestsPassed = true;
    
    try {
        // Run all tests
        allTestsPassed &= TestKbarManager();
        allTestsPassed &= TestSMA();
        allTestsPassed &= TestEMA();
        allTestsPassed &= TestMACD();
        allTestsPassed &= TestRSI();
        
        if (allTestsPassed) {
            std::cout << "\n=== ALL TECHNICAL INDICATOR TESTS PASSED ===\n";
        } else {
            std::cout << "\n=== SOME TESTS FAILED ===\n";
        }
    }
    catch (const std::exception& e) {
        std::cerr << "Exception during testing: " << e.what() << "\n";
        allTestsPassed = false;
    }
    
    // Cleanup
    KTPluginManager::Cleanup();
    log_close();
    
    return allTestsPassed ? 0 : 1;
}