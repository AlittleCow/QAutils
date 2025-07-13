/**
 * @file test_basic.cpp
 * @brief Basic test for KT Plugin infrastructure
 * 
 * This test verifies that the basic KT plugin infrastructure is working correctly.
 * It tests:
 * 1. Basic logging functionality
 * 2. KTFunctionBase class instantiation
 * 3. CALCINFO structure validation
 * 4. Data extraction utilities
 */

#include "../core/KTFunctionBase.h"
#include "../utils/log.h"
#include <iostream>
#include <vector>
#include <memory>

/**
 * @brief Simple test function implementation
 */
class TestKTFunction : public KTFunctionBase {
public:
    TestKTFunction() : KTFunctionBase(
        1001,                    // Function mark
        "TEST_FUNCTION",         // Function name
        "Test function for KT plugin infrastructure", // Description
        "Test",                  // Category
        10,                      // Min input count
        false,                   // Supports variable params
        1,                       // Expected param count
        false,                   // Requires financial data
        false                    // Requires extended data
    ) {}

    pKTFUNC GetKTFunctionPointer() const override {
        return TestFunction;
    }

private:
    static int TestFunction(CALCINFO* pData) {
        if (!ValidateCALCINFOStatic(pData, "TEST_FUNCTION")) {
            return -1;
        }

        LogFunctionCall("TEST_FUNCTION", pData);

        // Simple moving average calculation
        int period = static_cast<int>(GetConstantParam(pData, 0, 5.0f));
        if (period <= 0 || period > static_cast<int>(pData->nCount)) {
            period = 5;
        }

        // Initialize results
        InitializeResults(pData, 0.0f);

        // Calculate simple moving average
        for (int i = period - 1; i < static_cast<int>(pData->nCount); ++i) {
            float sum = 0.0f;
            for (int j = 0; j < period; ++j) {
                sum += pData->pData[i - j].close;
            }
            float ma = sum / period;
            WriteResult(pData, i, ma);
        }

        return period - 1; // Return first valid index
    }
};

/**
 * @brief Create test CALCINFO structure
 */
CALCINFO* CreateTestCALCINFO(int dataCount = 20) {
    CALCINFO* pData = new CALCINFO();
    memset(pData, 0, sizeof(CALCINFO));
    
    strcpy_s(pData->szLabel, "TEST001");
    strcpy_s(pData->szName, "Test Stock");
    pData->nCount = dataCount;
    pData->nType = DTYPE_DAY;
    
    // Allocate K-line data
    pData->pData = new STKDATA[dataCount];
    for (int i = 0; i < dataCount; ++i) {
        pData->pData[i].date = 20240101 + i;
        pData->pData[i].open = 10.0f + i * 0.1f;
        pData->pData[i].high = 10.5f + i * 0.1f;
        pData->pData[i].low = 9.5f + i * 0.1f;
        pData->pData[i].close = 10.2f + i * 0.1f;
        pData->pData[i].volume = 1000.0f + i * 10.0f;
        pData->pData[i].amount = 10000.0f + i * 100.0f;
    }
    
    // Allocate result buffer
    pData->ppResult = new float*[1];
    pData->ppResult[0] = new float[dataCount];
    pData->nResultCount = 1;
    
    // 分配参数
    pData->pParam = new CALCPARAM;
    pData->pParam->nParamCount = 1;
    pData->pParam->pParam = new float[1];
    pData->pParam->pParam[0] = 5.0f;  // 默认周期参数
    
    return pData;
}

/**
 * @brief Clean up test CALCINFO structure
 */
void CleanupTestCALCINFO(CALCINFO* pData) {
    if (pData) {
        delete[] pData->pData;
        if (pData->ppResult) {
            delete[] pData->ppResult[0];
            delete[] pData->ppResult;
        }
        if (pData->pParam) {
            delete[] pData->pParam->pParam;
            delete pData->pParam;
        }
        delete pData;
    }
}

/**
 * @brief Test basic logging functionality
 */
bool TestLogging() {
    std::cout << "Testing logging functionality..." << std::endl;
    
    Log::Init();
    Log::SetLevel(LOG_DEBUG);
    
    Log::Debug("Debug message test");
    Log::Info("Info message test");
    Log::Warn("Warning message test");
    Log::Error("Error message test");
    
    std::cout << "Logging test completed." << std::endl;
    return true;
}

/**
 * @brief Test KTFunctionBase functionality
 */
bool TestKTFunctionBase() {
    std::cout << "Testing KTFunctionBase functionality..." << std::endl;
    
    auto testFunc = std::make_shared<TestKTFunction>();
    
    // Test metadata
    if (testFunc->GetFunctionMark() != 1001) {
        std::cerr << "Function mark test failed" << std::endl;
        return false;
    }
    
    if (testFunc->GetFunctionName() != "TEST_FUNCTION") {
        std::cerr << "Function name test failed" << std::endl;
        return false;
    }
    
    if (!testFunc->IsValid()) {
        std::cerr << "Function validation test failed" << std::endl;
        return false;
    }
    
    std::cout << "Function info: " << std::endl;
    auto paramNames = testFunc->GetParameterNames();
        auto paramDescs = testFunc->GetParameterDescriptions();
        std::cout << "Parameters: ";
        for (size_t i = 0; i < paramNames.size(); ++i) {
            std::cout << paramNames[i] << " (" << paramDescs[i] << ")";
            if (i < paramNames.size() - 1) std::cout << ", ";
        }
        std::cout << std::endl;
    
    std::cout << "KTFunctionBase test completed." << std::endl;
    return true;
}

/**
 * @brief Test CALCINFO validation and data extraction
 */
bool TestCALCINFO() {
    std::cout << "Testing CALCINFO functionality..." << std::endl;
    
    CALCINFO* pData = CreateTestCALCINFO(20);
    
    // Test validation
    if (!KTFunctionBase::ValidateCALCINFOStatic(pData, "TEST")) {
        std::cerr << "CALCINFO validation failed" << std::endl;
        CleanupTestCALCINFO(pData);
        return false;
    }
    
    // Test data extraction
    auto closePrices = KTFunctionBase::ExtractClosePrice(pData);
    if (closePrices.size() != 20) {
        std::cerr << "Close price extraction failed" << std::endl;
        CleanupTestCALCINFO(pData);
        return false;
    }
    
    // Test parameter access
    float param = KTFunctionBase::GetConstantParam(pData, 0, 0.0f);
    if (param != 5.0f) {
        std::cerr << "Parameter access failed" << std::endl;
        CleanupTestCALCINFO(pData);
        return false;
    }
    
    std::cout << "CALCINFO test completed." << std::endl;
    CleanupTestCALCINFO(pData);
    return true;
}

/**
 * @brief Test function execution
 */
bool TestFunctionExecution() {
    std::cout << "Testing function execution..." << std::endl;
    
    auto testFunc = std::make_shared<TestKTFunction>();
    CALCINFO* pData = CreateTestCALCINFO(20);
    
    // Execute function
    pKTFUNC funcPtr = testFunc->GetKTFunctionPointer();
    int result = funcPtr(pData);
    
    if (result < 0) {
        std::cerr << "Function execution failed" << std::endl;
        CleanupTestCALCINFO(pData);
        return false;
    }
    
    // Check results
    bool hasValidResults = false;
    for (int i = result; i < static_cast<int>(pData->nCount); ++i) {
        if (pData->ppResult[0][i] > 0) {
            hasValidResults = true;
            std::cout << "Result[" << i << "] = " << pData->ppResult[0][i] << std::endl;
        }
    }
    
    if (!hasValidResults) {
        std::cerr << "No valid results generated" << std::endl;
        CleanupTestCALCINFO(pData);
        return false;
    }
    
    std::cout << "Function execution test completed." << std::endl;
    CleanupTestCALCINFO(pData);
    return true;
}

/**
 * @brief Main test function
 */
int main() {
    std::cout << "=== KT Plugin Infrastructure Test ===" << std::endl;
    
    bool allTestsPassed = true;
    
    // Enable debug mode
    KTFunctionBase::SetDebugMode(true);
    
    // Run tests
    allTestsPassed &= TestLogging();
    allTestsPassed &= TestKTFunctionBase();
    allTestsPassed &= TestCALCINFO();
    allTestsPassed &= TestFunctionExecution();
    
    // Cleanup
    Log::Close();
    
    if (allTestsPassed) {
        std::cout << "\n=== ALL TESTS PASSED ===" << std::endl;
        return 0;
    } else {
        std::cout << "\n=== SOME TESTS FAILED ===" << std::endl;
        return 1;
    }
}