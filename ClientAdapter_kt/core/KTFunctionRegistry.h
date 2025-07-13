#ifndef __KT_FUNCTION_REGISTRY_H__
#define __KT_FUNCTION_REGISTRY_H__

#include "IKTFunction.h"
#include "KTFunctionBase.h"
#include <map>
#include <vector>
#include <mutex>
#include <memory>

/**
 * @brief Registry for managing all KT functions
 * 
 * This class implements a singleton pattern to manage all registered KT functions.
 * It provides thread-safe registration, lookup, and enumeration of functions.
 * The registry also handles the conversion between OOP function objects and
 * the C-style interface expected by KT.
 */
class KTFunctionRegistry
{
private:
    std::map<unsigned short, KTFunctionPtr> m_functions;  /**< Map of function mark to function object */
    std::vector<KTFuncInfo> m_cFunctionInfos;             /**< C-style function info array for KT */
    mutable std::mutex m_mutex;                           /**< Thread safety mutex */
    bool m_isInitialized;                                 /**< Initialization flag */
    bool m_arrayProvided;                                 /**< Flag to prevent array rebuilding after KT access */

    // Private constructor for singleton
    KTFunctionRegistry();

public:
    /**
     * @brief Get the singleton instance
     * @return Reference to the registry instance
     */
    static KTFunctionRegistry& GetInstance();

    /**
     * @brief Destructor
     */
    ~KTFunctionRegistry() = default;

    // Delete copy constructor and assignment operator
    KTFunctionRegistry(const KTFunctionRegistry&) = delete;
    KTFunctionRegistry& operator=(const KTFunctionRegistry&) = delete;

    /**
     * @brief Register a new KT function
     * @param function Shared pointer to the function object
     * @return true if registration succeeded, false if function mark already exists
     */
    bool RegisterFunction(KTFunctionPtr function);

    /**
     * @brief Unregister a function by its mark
     * @param functionMark Function identifier to unregister
     * @return true if function was found and removed
     */
    bool UnregisterFunction(unsigned short functionMark);

    /**
     * @brief Get a function by its mark
     * @param functionMark Function identifier
     * @return Shared pointer to function object, or nullptr if not found
     */
    KTFunctionPtr GetFunction(unsigned short functionMark) const;

    /**
     * @brief Get all registered functions
     * @return Vector of all registered function objects
     */
    std::vector<KTFunctionPtr> GetAllFunctions() const;

    /**
     * @brief Get function count
     * @return Number of registered functions
     */
    size_t GetFunctionCount() const;

    /**
     * @brief Check if a function mark is already registered
     * @param functionMark Function identifier to check
     * @return true if function mark exists
     */
    bool IsFunctionRegistered(unsigned short functionMark) const;

    /**
     * @brief Get C-style function info array for KT registration
     * This method builds and returns the array expected by KT plugin interface
     * @return Pointer to null-terminated array of KTFuncInfo
     */
    KTFuncInfo* GetCFunctionInfoArray();

    /**
     * @brief Initialize the registry with default functions
     * This method can be overridden to register built-in functions
     */
    virtual void InitializeDefaultFunctions();

    /**
     * @brief Clear all registered functions
     */
    void Clear();

    /**
     * @brief Get registry statistics
     * @return String containing registry information
     */
    std::string GetRegistryInfo() const;

    /**
     * @brief Validate memory layout compatibility with KT
     * @return true if memory layout is compatible
     */
    bool ValidateMemoryLayout() const;

private:
    /**
     * @brief Rebuild the C-style function info array
     * This method is called whenever functions are added or removed
     */
    void RebuildCFunctionArray();

    /**
     * @brief Validate function before registration
     * @param function Function to validate
     * @return true if function is valid for registration
     */
    bool ValidateFunction(KTFunctionPtr function) const;
};

/**
 * @brief Convenience macro for registering functions
 */
#define REGISTER_KT_FUNCTION(functionClass, ...) \
    KTFunctionRegistry::GetInstance().RegisterFunction(std::make_shared<functionClass>(__VA_ARGS__))

#endif // __KT_FUNCTION_REGISTRY_H__