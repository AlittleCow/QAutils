#include "KTFunctionRegistry.h"
#include "../utils/log.h"
#include <algorithm>
#include <sstream>

/**
 * @brief Private constructor for singleton pattern
 */
KTFunctionRegistry::KTFunctionRegistry()
    : m_isInitialized(false), m_arrayProvided(false)
{
}

/**
 * @brief Get the singleton instance of the registry
 * @return Reference to the registry instance
 */
KTFunctionRegistry& KTFunctionRegistry::GetInstance()
{
    static KTFunctionRegistry instance;
    return instance;
}

/**
 * @brief Register a new KT function
 * @param function Shared pointer to function object
 * @return true if registration succeeded
 */
bool KTFunctionRegistry::RegisterFunction(KTFunctionPtr function)
{
    if (!ValidateFunction(function))
    {
        return false;
    }

    std::lock_guard<std::mutex> lock(m_mutex);
    
    // Prevent registration after array has been provided to KT
    if (m_arrayProvided)
    {
        log_error("Cannot register functions after array has been provided to KT");
        return false;
    }
    
    unsigned short functionMark = function->GetFunctionMark();
    
    // Check if function mark already exists
    if (m_functions.find(functionMark) != m_functions.end())
    {
        log_error("Function mark %d already registered", functionMark);
        return false;
    }

    // Register the function
    m_functions[functionMark] = function;
    
    // Rebuild C function array only if not yet provided to KT
    if (!m_arrayProvided)
    {
        RebuildCFunctionArray();
    }
    
    log_info("Registered function: %s (mark: %d)", function->GetFunctionName().c_str(), functionMark);
    
    return true;
}

/**
 * @brief Unregister a function by its mark
 * @param functionMark Function identifier
 * @return true if function was removed
 */
bool KTFunctionRegistry::UnregisterFunction(unsigned short functionMark)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    // Prevent unregistration after array has been provided to KT
    if (m_arrayProvided)
    {
        log_error("Cannot unregister functions after array has been provided to KT");
        return false;
    }
    
    auto it = m_functions.find(functionMark);
    if (it == m_functions.end())
    {
        return false;
    }

    std::string functionName = it->second->GetFunctionName();
    m_functions.erase(it);
    
    // Rebuild C function array only if not yet provided to KT
    if (!m_arrayProvided)
    {
        RebuildCFunctionArray();
    }
    
    log_info("Unregistered function: %s (mark: %d)", functionName.c_str(), functionMark);
    
    return true;
}

/**
 * @brief Get a function by its mark
 * @param functionMark Function identifier
 * @return Shared pointer to function object or nullptr
 */
KTFunctionPtr KTFunctionRegistry::GetFunction(unsigned short functionMark) const
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
std::vector<KTFunctionPtr> KTFunctionRegistry::GetAllFunctions() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    std::vector<KTFunctionPtr> functions;
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
size_t KTFunctionRegistry::GetFunctionCount() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_functions.size();
}

/**
 * @brief Check if a function mark is registered
 * @param functionMark Function identifier to check
 * @return true if function exists
 */
bool KTFunctionRegistry::IsFunctionRegistered(unsigned short functionMark) const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_functions.find(functionMark) != m_functions.end();
}

/**
 * @brief Get C-style function info array for KT
 * @return Pointer to function info array
 */
KTFuncInfo* KTFunctionRegistry::GetCFunctionInfoArray()
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    if (m_cFunctionInfos.empty())
    {
        RebuildCFunctionArray();
    }
    
    // Mark array as provided to KT - prevents future modifications
    // This ensures memory stability for KT which may hold onto this pointer
    if (!m_arrayProvided)
    {
        m_arrayProvided = true;
        log_debug("Function array provided to KT - registry is now locked for modifications");
    }
    
    return m_cFunctionInfos.data();
}

/**
 * @brief Initialize registry with default functions
 * Override this method in derived classes to add built-in functions
 */
void KTFunctionRegistry::InitializeDefaultFunctions()
{
    if (m_isInitialized)
    {
        return;
    }
    
    std::lock_guard<std::mutex> lock(m_mutex);
    
    // Default implementation does nothing
    // Derived classes or application code should register specific functions
    
    m_isInitialized = true;
    
    log_info("KT Function Registry initialized");
}

/**
 * @brief Clear all registered functions
 */
void KTFunctionRegistry::Clear()
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    size_t count = m_functions.size();
    m_functions.clear();
    m_cFunctionInfos.clear();
    m_isInitialized = false;
    m_arrayProvided = false;  // Reset the flag to allow new registrations
    
    log_info("Cleared %zu functions from registry", count);
}

/**
 * @brief Get registry statistics and information
 * @return String with registry details
 */
std::string KTFunctionRegistry::GetRegistryInfo() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    std::ostringstream oss;
    oss << "KT Function Registry Information:\n";
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
void KTFunctionRegistry::RebuildCFunctionArray()
{
    // Clear existing array
    m_cFunctionInfos.clear();
    
    // Reserve space for functions plus null terminator
    m_cFunctionInfos.reserve(m_functions.size() + 1);
    
    // Add each registered function
    for (const auto& pair : m_functions)
    {
        auto function = pair.second;
        
        KTFuncInfo info;
        info.nFuncMark = function->GetFunctionMark();
        info.pCallFunc = function->GetKTFunctionPointer();
        
        // Validate the function pointer is not null
        if (info.pCallFunc == nullptr)
        {
            log_error("Function %s (mark %d) returned null function pointer", 
                     function->GetFunctionName().c_str(), info.nFuncMark);
            continue;
        }
        
        // Log detailed registration info
        // log_debug("Registering function: Mark=%d, Name='%s', FuncPtr=%p", 
        //          info.nFuncMark, function->GetFunctionName().c_str(), info.pCallFunc);
        
        m_cFunctionInfos.push_back(info);
    }
    
    // Add null terminator - CRITICAL for KT compatibility
    KTFuncInfo nullInfo;
    nullInfo.nFuncMark = 0;
    nullInfo.pCallFunc = nullptr;
    m_cFunctionInfos.push_back(nullInfo);
    
    // Validate memory layout matches expectations
    if (!m_cFunctionInfos.empty())
    {
        // Ensure the array is contiguous in memory
        size_t expectedSize = m_cFunctionInfos.size() * sizeof(KTFuncInfo);
        log_debug("Built function array: %zu functions + 1 terminator, %zu bytes total", 
                 m_cFunctionInfos.size() - 1, expectedSize);
        
        // Verify the last entry is the null terminator
        const auto& lastEntry = m_cFunctionInfos.back();
        if (lastEntry.nFuncMark != 0 || lastEntry.pCallFunc != nullptr)
        {
            log_error("Function array null terminator is invalid!");
        }
    }
}

/**
 * @brief Validate a function before registration
 * @param function Function to validate
 * @return true if function is valid
 */
bool KTFunctionRegistry::ValidateFunction(KTFunctionPtr function) const
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
    
    if (function->GetKTFunctionPointer() == nullptr)
    {
        log_error("Function must provide valid KT function pointer");
        return false;
    }
    
    return true;
}

/**
 * @brief Validate memory layout compatibility with KT
 * @return true if memory layout is compatible
 */
bool KTFunctionRegistry::ValidateMemoryLayout() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    
    if (m_cFunctionInfos.empty())
    {
        log_debug("Function array is empty - nothing to validate");
        return true;
    }
    
    // Check structure size and alignment
    size_t expectedStructSize = sizeof(KTFuncInfo);
    log_debug("KTFuncInfo size: %zu bytes", expectedStructSize);
    
    // Verify the array is properly null-terminated
    const auto& lastEntry = m_cFunctionInfos.back();
    if (lastEntry.nFuncMark != 0 || lastEntry.pCallFunc != nullptr)
    {
        log_error("Function array is not properly null-terminated");
        return false;
    }
    
    // Check that all function pointers are valid
    for (size_t i = 0; i < m_cFunctionInfos.size() - 1; ++i) // Skip null terminator
    {
        const auto& info = m_cFunctionInfos[i];
        if (info.nFuncMark == 0)
        {
            log_error("Function at index %zu has invalid mark 0", i);
            return false;
        }
        if (info.pCallFunc == nullptr)
        {
            log_error("Function at index %zu has null function pointer", i);
            return false;
        }
    }
    
    // Verify memory is contiguous (vector guarantees this, but let's be explicit)
    if (m_cFunctionInfos.size() > 1)
    {
        const void* firstPtr = &m_cFunctionInfos[0];
        const void* secondPtr = &m_cFunctionInfos[1];
        ptrdiff_t actualDistance = static_cast<const char*>(secondPtr) - static_cast<const char*>(firstPtr);
        
        if (actualDistance != static_cast<ptrdiff_t>(sizeof(KTFuncInfo)))
        {
            log_error("Function array elements are not contiguous: expected %zu bytes, got %td bytes",
                     sizeof(KTFuncInfo), actualDistance);
            return false;
        }
    }
    
    log_debug("Memory layout validation passed: %zu functions + 1 terminator", 
             m_cFunctionInfos.size() - 1);
    return true;
}