#include "TdxFunctionRegistry.h"
#include "../utils/log.h"
#include <algorithm>
#include <sstream>

/**
 * @brief Private constructor for singleton pattern
 */
TdxFunctionRegistry::TdxFunctionRegistry()
    : m_isInitialized(false)
{
}

/**
 * @brief Get the singleton instance of the registry
 * @return Reference to the registry instance
 */
TdxFunctionRegistry& TdxFunctionRegistry::GetInstance()
{
    static TdxFunctionRegistry instance;
    return instance;
}

/**
 * @brief Register a new TDX function
 * @param function Shared pointer to function object
 * @return true if registration succeeded
 */
bool TdxFunctionRegistry::RegisterFunction(TdxFunctionPtr function)
{
    if (!ValidateFunction(function))
    {
        return false;
    }

    std::lock_guard<std::mutex> lock(m_mutex);
    
    unsigned short functionMark = function->GetFunctionMark();
    
    // Check if function mark already exists
    if (m_functions.find(functionMark) != m_functions.end())
    {
        log_error("Function mark %d already registered", functionMark);
        return false;
    }

    // Register the function
    m_functions[functionMark] = function;
    
    // Rebuild C function array
    RebuildCFunctionArray();
    
    log_info("Registered function: %s (mark: %d)", function->GetFunctionName().c_str(), functionMark);
    
    return true;
}

/**
 * @brief Unregister a function by its mark
 * @param functionMark Function identifier
 * @return true if function was removed
 */
bool TdxFunctionRegistry::UnregisterFunction(unsigned short functionMark)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    auto it = m_functions.find(functionMark);
    if (it == m_functions.end())
    {
        return false;
    }

    std::string functionName = it->second->GetFunctionName();
    m_functions.erase(it);
    
    // Rebuild C function array
    RebuildCFunctionArray();
    
    log_info("Unregistered function: %s (mark: %d)", functionName.c_str(), functionMark);
    
    return true;
}

/**
 * @brief Get a function by its mark
 * @param functionMark Function identifier
 * @return Shared pointer to function object or nullptr
 */
TdxFunctionPtr TdxFunctionRegistry::GetFunction(unsigned short functionMark) const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    auto it = m_functions.find(functionMark);
    if (it != m_functions.end())
    {
        return it->second;
    }
    return nullptr;
}

/**
 * @brief Get all registered functions
 * @return Vector of all function objects
 */
std::vector<TdxFunctionPtr> TdxFunctionRegistry::GetAllFunctions() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    std::vector<TdxFunctionPtr> functions;
    functions.reserve(m_functions.size());
    
    for (const auto& pair : m_functions)
    {
        functions.push_back(pair.second);
    }
    
    return functions;
}

/**
 * @brief Get the number of registered functions
 * @return Function count
 */
size_t TdxFunctionRegistry::GetFunctionCount() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_functions.size();
}

/**
 * @brief Check if a function mark is registered
 * @param functionMark Function identifier to check
 * @return true if function exists
 */
bool TdxFunctionRegistry::IsFunctionRegistered(unsigned short functionMark) const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_functions.find(functionMark) != m_functions.end();
}

/**
 * @brief Get C-style function info array for TDX
 * @return Pointer to function info array
 */
PluginTCalcFuncInfo* TdxFunctionRegistry::GetCFunctionInfoArray()
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    if (m_cFunctionInfos.empty())
    {
        RebuildCFunctionArray();
    }
    
    return m_cFunctionInfos.data();
}

/**
 * @brief Initialize registry with default functions
 * Override this method in derived classes to add built-in functions
 */
void TdxFunctionRegistry::InitializeDefaultFunctions()
{
    if (m_isInitialized)
    {
        return;
    }
    
    std::lock_guard<std::mutex> lock(m_mutex);
    
    // Default implementation does nothing
    // Derived classes or application code should register specific functions
    
    m_isInitialized = true;
    
    log_info("TDX Function Registry initialized");
}

/**
 * @brief Clear all registered functions
 */
void TdxFunctionRegistry::Clear()
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    size_t count = m_functions.size();
    m_functions.clear();
    m_cFunctionInfos.clear();
    m_isInitialized = false;
    
    log_info("Cleared %zu functions from registry", count);
}

/**
 * @brief Get registry statistics and information
 * @return String with registry details
 */
std::string TdxFunctionRegistry::GetRegistryInfo() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    std::ostringstream oss;
    oss << "TDX Function Registry Information:\n";
    oss << "  Total Functions: " << m_functions.size() << "\n";
    oss << "  Initialized: " << (m_isInitialized ? "Yes" : "No") << "\n";
    oss << "  Registered Functions:\n";
    
    for (const auto& pair : m_functions)
    {
        oss << "    Mark " << pair.first << ": " 
            << pair.second->GetFunctionName() << " - " 
            << pair.second->GetDescription() << "\n";
    }
    
    return oss.str();
}

/**
 * @brief Rebuild the C-style function info array
 * This method is called when functions are added or removed
 */
void TdxFunctionRegistry::RebuildCFunctionArray()
{
    // Clear existing array
    m_cFunctionInfos.clear();
    
    // Reserve space for functions plus null terminator
    m_cFunctionInfos.reserve(m_functions.size() + 1);
    
    // Add each registered function
    for (const auto& pair : m_functions)
    {
        auto function = pair.second;
        
        // Set current instance for C wrapper
        if (auto baseFunction = std::dynamic_pointer_cast<TdxFunctionBase>(function))
        {
            baseFunction->SetCurrentInstance();
        }
        
        PluginTCalcFuncInfo info;
        info.nFuncMark = function->GetFunctionMark();
        info.pCallFunc = function->GetCFunctionPointer();
        
        m_cFunctionInfos.push_back(info);
    }
    
    // Add null terminator
    PluginTCalcFuncInfo nullInfo;
    nullInfo.nFuncMark = 0;
    nullInfo.pCallFunc = nullptr;
    m_cFunctionInfos.push_back(nullInfo);
}

/**
 * @brief Validate a function before registration
 * @param function Function to validate
 * @return true if function is valid
 */
bool TdxFunctionRegistry::ValidateFunction(TdxFunctionPtr function) const
{
    if (!function)
    {
        log_error("Cannot register null function");
        return false;
    }
    
    if (function->GetFunctionMark() == 0)
    {
        log_error("Function mark cannot be 0 (reserved for null terminator)");
        return false;
    }
    
    if (function->GetFunctionName().empty())
    {
        log_error("Function name cannot be empty");
        return false;
    }
    
    if (function->GetCFunctionPointer() == nullptr)
    {
        log_error("Function must provide valid C function pointer");
        return false;
    }
    
    return true;
} 