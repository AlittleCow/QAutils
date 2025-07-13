/**
 * @file test_direct_exports.cpp
 * @brief Test direct export functions for KT Trading Platform
 * 
 * This file tests the thin wrapper functions that are directly exported
 * for KT Trading Platform to call by name.
 */

#include "../core/KTPluginMain.h"
#include "../core/IKTFunction.h"
#include "../utils/log.h"
#include <iostream>
#include <vector>
#include <memory>
#include <cmath>

/**
 * @brief Generate test K-bar data
 */
std::vector<STKDATA> GenerateTestKBarData(int count, float basePrice = 100.0f)
{
    std::vector<STKDATA> data(count);
    
    for (int i = 0; i < count; ++i) {
        float price = basePrice + std::sin(i * 0.1f) * 10.0f + i * 0.1f;
        data[i].open = price - 0.5f;
        data[i].high = price + 1.0f;
        data[i].low = price - 1.0f;
        data[i].close = price;
        data[i].volume = 1000 + i * 10;
        data[i].amount = data[i].close * data[i].volume;
        data[i].date = 20240101 + i;
        data[i].time = 930 + (i % 240); // Trading hours
    }
    
    return data;
}

/**
 * @brief Create CALCINFO structure for testing
 */
std::unique_ptr<CALCINFO> CreateTestCALCINFO(const std::vector<STKDATA>& data, 
                                              int resultCount = 1,
                                              const std::vector<float>& params = {})
{
    auto calcInfo = std::make_unique<CALCINFO>();
    
    // Basic information
    strcpy_s(calcInfo->szLabel, sizeof(calcInfo->szLabel), "TEST");
    strcpy_s(calcInfo->szName, sizeof(calcInfo->szName), "Test Stock");
    calcInfo->nType = DTYPE_DAY;
    calcInfo->nCount = static_cast<int>(data.size());
    
    // K-bar data
    calcInfo->pData = const_cast<STKDATA*>(data.data());
    
    // Parameters
    calcInfo->nParamCount = static_cast<int>(params.size());
    if (!params.empty()) {
        calcInfo->pParam = const_cast<float*>(params.data());
    } else {
        calcInfo->pParam = nullptr;
    }
    
    // Result arrays
    calcInfo->nResultCount = resultCount;
    calcInfo->ppResult = new float*[resultCount];
    for (int i = 0; i < resultCount; ++i) {
        calcInfo->ppResult[i] = new float[data.size()];
        // Initialize with NaN
        for (size_t j = 0; j < data.size(); ++j) {
            calcInfo->ppResult[i][j] = std::numeric_limits<float>::quiet_NaN();
        }
    }
    
    // Extended data (optional)
    calcInfo->pDataEx = nullptr;
    calcInfo->pFinanceData = nullptr;
    
    return calcInfo;
}

/**
 * @brief Clean up CALCINFO structure
 */
void CleanupCALCINFO(CALCINFO* calcInfo)
{
    if (calcInfo && calcInfo->ppResult) {
        for (int i = 0; i < calcInfo->nResultCount; ++i) {
            delete[] calcInfo->ppResult[i];
        }
        delete[] calcInfo->ppResult;
        calcInfo->ppResult = nullptr;
    }
}

/**
 * @brief Test KT_SMA direct export function
 */
bool TestDirectSMA()
{
    std::cout << "\n=== Testing Direct Export KT_SMA ===\n";
    
    auto data = GenerateTestKBarData(50);
    auto calcInfo = CreateTestCALCINFO(data, 1, {20.0f}); // 20-period SMA
    
    // Call the direct export function
    BOOL result = KT_SMA(calcInfo.get());
    
    if (result) {
        std::cout << "KT_SMA call successful!\n";
        
        // Display some results
        std::cout << "First 10 SMA values:\n";
        for (int i = 0; i < 10 && i < calcInfo->nCount; ++i) {
            if (!std::isnan(calcInfo->ppResult[0][i])) {
                std::cout << "SMA[" << i << "] = " << calcInfo->ppResult[0][i] << "\n";
            } else {
                std::cout << "SMA[" << i << "] = NaN (insufficient data)\n";
            }
        }
        
        // Check if we have valid results after the period
        bool hasValidResults = false;
        for (int i = 19; i < calcInfo->nCount; ++i) { // After 20-period
            if (!std::isnan(calcInfo->ppResult[0][i])) {
                hasValidResults = true;
                break;
            }
        }
        
        if (hasValidResults) {
            std::cout << "✓ KT_SMA test PASSED - Valid results found\n";
        } else {
            std::cout << "✗ KT_SMA test FAILED - No valid results\n";
            result = FALSE;
        }
    } else {
        std::cout << "✗ KT_SMA call failed!\n";
    }
    
    CleanupCALCINFO(calcInfo.get());
    return result == TRUE;
}

/**
 * @brief Test KT_EMA direct export function
 */
bool TestDirectEMA()
{
    std::cout << "\n=== Testing Direct Export KT_EMA ===\n";
    
    auto data = GenerateTestKBarData(50);
    auto calcInfo = CreateTestCALCINFO(data, 1, {12.0f}); // 12-period EMA
    
    // Call the direct export function
    BOOL result = KT_EMA(calcInfo.get());
    
    if (result) {
        std::cout << "KT_EMA call successful!\n";
        
        // Display some results
        std::cout << "First 10 EMA values:\n";
        for (int i = 0; i < 10 && i < calcInfo->nCount; ++i) {
            if (!std::isnan(calcInfo->ppResult[0][i])) {
                std::cout << "EMA[" << i << "] = " << calcInfo->ppResult[0][i] << "\n";
            } else {
                std::cout << "EMA[" << i << "] = NaN\n";
            }
        }
        
        std::cout << "✓ KT_EMA test PASSED\n";
    } else {
        std::cout << "✗ KT_EMA call failed!\n";
    }
    
    CleanupCALCINFO(calcInfo.get());
    return result == TRUE;
}

/**
 * @brief Test KT_RSI direct export function
 */
bool TestDirectRSI()
{
    std::cout << "\n=== Testing Direct Export KT_RSI ===\n";
    
    auto data = GenerateTestKBarData(50);
    auto calcInfo = CreateTestCALCINFO(data, 1, {14.0f}); // 14-period RSI
    
    // Call the direct export function
    BOOL result = KT_RSI(calcInfo.get());
    
    if (result) {
        std::cout << "KT_RSI call successful!\n";
        
        // Display some results (RSI should be between 0-100)
        std::cout << "Last 10 RSI values:\n";
        for (int i = calcInfo->nCount - 10; i < calcInfo->nCount; ++i) {
            if (i >= 0 && !std::isnan(calcInfo->ppResult[0][i])) {
                std::cout << "RSI[" << i << "] = " << calcInfo->ppResult[0][i] << "\n";
            }
        }
        
        std::cout << "✓ KT_RSI test PASSED\n";
    } else {
        std::cout << "✗ KT_RSI call failed!\n";
    }
    
    CleanupCALCINFO(calcInfo.get());
    return result == TRUE;
}

/**
 * @brief Test KT_MACD direct export function
 */
bool TestDirectMACD()
{
    std::cout << "\n=== Testing Direct Export KT_MACD ===\n";
    
    auto data = GenerateTestKBarData(50);
    auto calcInfo = CreateTestCALCINFO(data, 3, {12.0f, 26.0f, 9.0f}); // MACD(12,26,9)
    
    // Call the direct export function
    BOOL result = KT_MACD(calcInfo.get());
    
    if (result) {
        std::cout << "KT_MACD call successful!\n";
        
        // Display some results
        std::cout << "Last 5 MACD values:\n";
        for (int i = calcInfo->nCount - 5; i < calcInfo->nCount; ++i) {
            if (i >= 0) {
                std::cout << "MACD[" << i << "] = ";
                std::cout << "Line: " << calcInfo->ppResult[0][i] << ", ";
                std::cout << "Signal: " << calcInfo->ppResult[1][i] << ", ";
                std::cout << "Histogram: " << calcInfo->ppResult[2][i] << "\n";
            }
        }
        
        std::cout << "✓ KT_MACD test PASSED\n";
    } else {
        std::cout << "✗ KT_MACD call failed!\n";
    }
    
    CleanupCALCINFO(calcInfo.get());
    return result == TRUE;
}

/**
 * @brief Main test function
 */
int main()
{
    std::cout << "=== QAUtils KT Plugin Direct Export Function Tests ===\n";
    
    // Initialize logging
    log_init();
    log_set_level(LOG_DEBUG);
    
    int passedTests = 0;
    int totalTests = 0;
    
    // Test direct export functions
    totalTests++;
    if (TestDirectSMA()) passedTests++;
    
    totalTests++;
    if (TestDirectEMA()) passedTests++;
    
    totalTests++;
    if (TestDirectRSI()) passedTests++;
    
    totalTests++;
    if (TestDirectMACD()) passedTests++;
    
    // Summary
    std::cout << "\n=== Test Summary ===\n";
    std::cout << "Passed: " << passedTests << "/" << totalTests << " tests\n";
    
    if (passedTests == totalTests) {
        std::cout << "✓ All direct export function tests PASSED!\n";
        std::cout << "\nKT Trading Platform can now call these functions directly:\n";
        std::cout << "- KT_SMA(CALCINFO* pCalcInfo)\n";
        std::cout << "- KT_EMA(CALCINFO* pCalcInfo)\n";
        std::cout << "- KT_RSI(CALCINFO* pCalcInfo)\n";
        std::cout << "- KT_MACD(CALCINFO* pCalcInfo)\n";
        std::cout << "\nExample KT formula usage:\n";
        std::cout << "SMA20 := KT_SMA(CLOSE, 20);\n";
        std::cout << "EMA12 := KT_EMA(CLOSE, 12);\n";
    } else {
        std::cout << "✗ Some tests FAILED. Check the log for details.\n";
    }
    
    log_close();
    return (passedTests == totalTests) ? 0 : 1;
}