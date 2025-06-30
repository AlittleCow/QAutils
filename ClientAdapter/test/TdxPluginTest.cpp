#include "TdxPluginMain.h"
#include "TdxExampleFunctions.h"
#include "TdxUtilities.h"
#include <iostream>
#include <vector>
#include <cassert>

/**
 * @brief Test program for QAUtils TDX Plugin
 * 
 * This program tests the functionality of the TDX plugin framework
 * without requiring TDX to be installed.
 */

// Test data
const int TEST_DATA_SIZE = 10;
float g_testInputA[TEST_DATA_SIZE] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f, 6.0f, 7.0f, 8.0f, 9.0f, 10.0f};
float g_testInputB[TEST_DATA_SIZE] = {2.0f, 4.0f, 6.0f, 8.0f, 10.0f, 12.0f, 14.0f, 16.0f, 18.0f, 20.0f};
float g_testInputC[TEST_DATA_SIZE] = {0.5f, 1.0f, 1.5f, 2.0f, 2.5f, 3.0f, 3.5f, 4.0f, 4.5f, 5.0f};
float g_testOutput[TEST_DATA_SIZE];

/**
 * @brief Test registry functionality
 */
void TestRegistry()
{
    std::cout << "\n=== Testing Registry Functionality ===" << std::endl;
    
    auto& registry = TdxFunctionRegistry::GetInstance();
    
    // Test registration
    auto seqFunc = std::make_shared<SequenceFunction>();
    bool success = registry.RegisterFunction(seqFunc);
    assert(success);
    if (!success) {
        std::cerr << "Failed to register function" << std::endl;
    }
    std::cout << "✓ Function registration successful" << std::endl;
    
    // Test duplicate registration (should fail)
    auto seqFunc2 = std::make_shared<SequenceFunction>();
    bool duplicate = registry.RegisterFunction(seqFunc2);
    assert(!duplicate);
    if (duplicate) {
        std::cerr << "Duplicate registration should have failed" << std::endl;
    }
    std::cout << "✓ Duplicate registration properly rejected" << std::endl;
    
    // Test function lookup
    auto foundFunc = registry.GetFunction(1);
    assert(foundFunc != nullptr);
    assert(foundFunc->GetFunctionMark() == 1);
    std::cout << "✓ Function lookup successful" << std::endl;
    
    // Test function count
    size_t count = registry.GetFunctionCount();
    assert(count >= 1);
    std::cout << "✓ Function count: " << count << std::endl;
    
    // Test registry info
    std::string info = registry.GetRegistryInfo();
    assert(!info.empty());
    std::cout << "✓ Registry info generated" << std::endl;
}

/**
 * @brief Test sequence function
 */
void TestSequenceFunction()
{
    std::cout << "\n=== Testing Sequence Function ===" << std::endl;
    
    SequenceFunction func;
    
    // Test basic functionality
    bool success = func.Execute(TEST_DATA_SIZE, g_testOutput, nullptr, nullptr, nullptr);
    assert(success);
    if (!success) {
        std::cerr << "Sequence function execution failed" << std::endl;
    }
    
    // Verify output
    for (int i = 0; i < TEST_DATA_SIZE; ++i)
    {
        assert(g_testOutput[i] == static_cast<float>(i));
    }
    
    std::cout << "✓ Sequence function test passed" << std::endl;
    std::cout << "  Output: ";
    for (int i = 0; i < TEST_DATA_SIZE; ++i)
    {
        std::cout << g_testOutput[i] << " ";
    }
    std::cout << std::endl;
}

/**
 * @brief Test average function
 */
void TestAverageFunction()
{
    std::cout << "\n=== Testing Average Function ===" << std::endl;
    
    AverageFunction func;
    
    // Test basic functionality
    bool success = func.Execute(TEST_DATA_SIZE, g_testOutput, g_testInputA, g_testInputB, g_testInputC);
    assert(success);
    if (!success) {
        std::cerr << "Average function execution failed" << std::endl;
    }
    
    // Verify output (should be average of three inputs)
    for (int i = 0; i < TEST_DATA_SIZE; ++i)
    {
        float expected = (g_testInputA[i] + g_testInputB[i] + g_testInputC[i]) / 3.0f;
        assert(std::abs(g_testOutput[i] - expected) < 0.001f);
        if (std::abs(g_testOutput[i] - expected) >= 0.001f) {
            std::cerr << "Average calculation mismatch at index " << i << std::endl;
        }
    }
    
    std::cout << "✓ Average function test passed" << std::endl;
    std::cout << "  Sample output: " << g_testOutput[0] << ", " << g_testOutput[1] << ", " << g_testOutput[2] << std::endl;
    
    // Test validation (should fail with null input)
    success = func.Execute(TEST_DATA_SIZE, g_testOutput, nullptr, g_testInputB, g_testInputC);
    assert(!success);
    if (success) {
        std::cerr << "Validation should have failed with null input" << std::endl;
    }
    std::cout << "✓ Input validation working correctly" << std::endl;
}

/**
 * @brief Test SMA function
 */
void TestSMAFunction()
{
    std::cout << "\n=== Testing SMA Function ===" << std::endl;
    
    SimpleMovingAverageFunction func;
    
    // Period parameter (use period of 3)
    float period[1] = {3.0f};
    
    // Test basic functionality
    bool success = func.Execute(TEST_DATA_SIZE, g_testOutput, g_testInputA, period, nullptr);
    assert(success);
    if (!success) {
        std::cerr << "SMA function execution failed" << std::endl;
    }
    
    // Verify first valid SMA value (index 2, period 3)
    float expectedSMA = (g_testInputA[0] + g_testInputA[1] + g_testInputA[2]) / 3.0f;
    assert(std::abs(g_testOutput[2] - expectedSMA) < 0.001f);
    if (std::abs(g_testOutput[2] - expectedSMA) >= 0.001f) {
        std::cerr << "SMA calculation mismatch: expected " << expectedSMA << ", got " << g_testOutput[2] << std::endl;
    }
    
    std::cout << "✓ SMA function test passed" << std::endl;
    std::cout << "  Sample SMA values: ";
    for (int i = 2; i < std::min(6, TEST_DATA_SIZE); ++i)
    {
        std::cout << g_testOutput[i] << " ";
    }
    std::cout << std::endl;
}

/**
 * @brief Test EMA function
 */
void TestEMAFunction()
{
    std::cout << "\n=== Testing EMA Function ===" << std::endl;
    
    ExponentialMovingAverageFunction func;
    
    // Period parameter (use period of 5)
    float period[1] = {5.0f};
    
    // Test basic functionality
    bool success = func.Execute(TEST_DATA_SIZE, g_testOutput, g_testInputA, period, nullptr);
    assert(success);
    if (!success) {
        std::cerr << "EMA function execution failed" << std::endl;
    }
    
    // Verify first value equals input
    assert(g_testOutput[0] == g_testInputA[0]);
    
    std::cout << "✓ EMA function test passed" << std::endl;
    std::cout << "  Sample EMA values: ";
    for (int i = 0; i < std::min(5, TEST_DATA_SIZE); ++i)
    {
        std::cout << g_testOutput[i] << " ";
    }
    std::cout << std::endl;
}

/**
 * @brief Test utility functions
 */
void TestUtilities()
{
    std::cout << "\n=== Testing Utility Functions ===" << std::endl;
    
    // Test array validation
    bool valid = TdxUtilities::ValidateArray(g_testInputA, TEST_DATA_SIZE, "TestArray");
    assert(valid);
    if (!valid) {
        std::cerr << "Array validation failed" << std::endl;
    }
    std::cout << "✓ Array validation test passed" << std::endl;
    
    // Test array statistics
    float sum = TdxUtilities::SumArray(g_testInputA, TEST_DATA_SIZE);
    float mean = TdxUtilities::MeanArray(g_testInputA, TEST_DATA_SIZE);
    float minVal = TdxUtilities::MinArray(g_testInputA, TEST_DATA_SIZE);
    float maxVal = TdxUtilities::MaxArray(g_testInputA, TEST_DATA_SIZE);
    
    assert(sum == 55.0f); // 1+2+...+10 = 55
    assert(mean == 5.5f); // 55/10 = 5.5
    assert(minVal == 1.0f);
    assert(maxVal == 10.0f);
    
    std::cout << "✓ Array statistics test passed" << std::endl;
    std::cout << "  Sum: " << sum << ", Mean: " << mean << ", Min: " << minVal << ", Max: " << maxVal << std::endl;
    
    // Test safe operations
    float result = TdxUtilities::SafeDivide(10.0f, 2.0f, 0.0f);
    assert(result == 5.0f);
    
    result = TdxUtilities::SafeDivide(10.0f, 0.0f, -1.0f);
    assert(result == -1.0f);
    
    std::cout << "✓ Safe operations test passed" << std::endl;
    
    // Test performance timer
    TdxPerformanceTimer timer;
    timer.Start();
    
    // Simulate some work
    volatile int dummy = 0;
    for (int i = 0; i < 1000000; ++i)
    {
        dummy += i;
    }
    
    timer.Stop();
    double elapsed = timer.GetElapsedMilliseconds();
    assert(elapsed >= 0.0);
    
    std::cout << "✓ Performance timer test passed (elapsed: " << elapsed << " ms)" << std::endl;
}

/**
 * @brief Test plugin initialization
 */
void TestPluginInitialization()
{
    std::cout << "\n=== Testing Plugin Initialization ===" << std::endl;
    
    // Test initialization
    bool success = TdxPluginManager::Initialize();
    assert(success);
    std::cout << "✓ Plugin initialization successful" << std::endl;
    
    // Test multiple initialization (should be safe)
    success = TdxPluginManager::Initialize();
    assert(success);
    std::cout << "✓ Multiple initialization safe" << std::endl;
    
    // Test plugin info
    std::string info = TdxPluginManager::GetPluginInfo();
    assert(!info.empty());
    std::cout << "✓ Plugin info generated" << std::endl;
    
    // Test C-style registration
    PluginTCalcFuncInfo* pInfo = nullptr;
    BOOL result = RegisterTdxFunc(&pInfo);
    assert(result == TRUE);
    assert(pInfo != nullptr);
    if (result != TRUE || pInfo == nullptr) {
        std::cerr << "C-style registration failed" << std::endl;
    }
    std::cout << "✓ C-style registration successful" << std::endl;
    
    // Count registered functions
    int functionCount = 0;
    while (pInfo[functionCount].nFuncMark != 0)
    {
        functionCount++;
    }
    std::cout << "  Registered " << functionCount << " functions via C interface" << std::endl;
}

/**
 * @brief Main test function
 */
int main()
{
    std::cout << "QAUtils TDX Plugin Test Program" << std::endl;
    std::cout << "===============================" << std::endl;
    
    try
    {
        // Run all tests
        TestRegistry();
        TestSequenceFunction();
        TestAverageFunction();
        TestSMAFunction();
        TestEMAFunction();
        TestUtilities();
        TestPluginInitialization();
        
        std::cout << "\n=== All Tests Completed Successfully ===" << std::endl;
        std::cout << "✓ Registry functionality working" << std::endl;
        std::cout << "✓ All example functions working" << std::endl;
        std::cout << "✓ Utility functions working" << std::endl;
        std::cout << "✓ Plugin initialization working" << std::endl;
        std::cout << "✓ C-style interface working" << std::endl;
        
        // Display plugin information
        std::cout << "\n" << TdxPluginManager::GetPluginInfo() << std::endl;
        
        return 0;
    }
    catch (const std::exception& e)
    {
        std::cerr << "❌ Test failed with exception: " << e.what() << std::endl;
        return 1;
    }
    catch (...)
    {
        std::cerr << "❌ Test failed with unknown exception" << std::endl;
        return 1;
    }
} 