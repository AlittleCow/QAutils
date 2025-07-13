#ifndef __IKT_FUNCTION_H__
#define __IKT_FUNCTION_H__

#include <windows.h>
#include <string>
#include <vector>
#include <memory>

#pragma pack(push, 1)

// KT Data Type Definition
enum DATA_TYPE
{
    DTYPE_NONE = 0,
    DTYPE_MIN1 = 1,     // 1 minute
    DTYPE_MIN5 = 2,     // 5 minutes
    DTYPE_MIN15 = 3,    // 15 minutes
    DTYPE_MIN30 = 4,    // 30 minutes
    DTYPE_MIN60 = 5,    // 60 minutes
    DTYPE_DAY = 6,      // Daily
    DTYPE_WEEK = 7,     // Weekly
    DTYPE_MONTH = 8,    // Monthly
    DTYPE_YEAR = 9,     // Yearly
    DTYPE_SEASON = 10,  // Quarterly
    DTYPE_HALFYEAR = 11 // Half-yearly
};

// KT K-line data structure
typedef struct tagSTKDATA
{
    DWORD date;         // Date (YYYYMMDD)
    DWORD time;         // Time (HHMMSS)
    float open;         // Open price
    float high;         // High price
    float low;          // Low price
    float close;        // Close price
    float volume;       // Volume
    float amount;       // Amount
} STKDATA;

// Extended KT data structure
typedef struct tagSTKDATAEx
{
    STKDATA stkdata;    // Basic K-line data
    float reserve1;     // Reserved field 1
    float reserve2;     // Reserved field 2
    float reserve3;     // Reserved field 3
    float reserve4;     // Reserved field 4
} STKDATAEx;

// KT calculation parameter structure
typedef struct tagCALCPARAM
{
    int nParamCount;    // Parameter count
    float* pParam;      // Parameter array
} CALCPARAM;

// KT dividend/split data structure
typedef struct tagSPLITDATA
{
    DWORD date;         // Ex-dividend date
    float fCashDiv;     // Cash dividend per share
    float fStkDiv;      // Stock dividend ratio
    float fStkSplit;    // Stock split ratio
    float fAllotPrice;  // Rights offering price
    float fAllotRatio;  // Rights offering ratio
} SPLITDATA;

// KT main calculation info structure
typedef struct tagCALCINFO
{
    // Basic info
    char szLabel[64];           // Stock code
    char szName[64];            // Stock name
    DATA_TYPE nType;            // Data type
    int nStart;                 // Start position
    int nCount;                 // Data count
    
    // K-line data
    STKDATA* pData;             // K-line data array
    STKDATAEx* pDataEx;         // Extended data array
    
    // Parameters
    CALCPARAM* pParam;          // Calculation parameters
    
    // Financial data
    SPLITDATA* pSplitData;      // Dividend/split data
    int nSplitDataCount;        // Dividend/split data count
    
    // Output
    float** ppResult;           // Result arrays
    int nResultCount;           // Result array count
    
    // Reserved
    void* pReserved1;
    void* pReserved2;
    void* pReserved3;
    void* pReserved4;
} CALCINFO;

#pragma pack(pop)

// KT function pointer type
typedef BOOL (*pKTFUNC)(CALCINFO* pCalcInfo);

// KT function info structure for registration
typedef struct tagKTFuncInfo
{
    unsigned short nFuncMark;   // Function identifier
    pKTFUNC pCallFunc;          // Function pointer
} KTFuncInfo;

/**
 * @brief Interface for KT functions
 * 
 * This interface defines the contract that all KT functions must implement.
 * It provides metadata about the function and the actual computation logic.
 */
class IKTFunction
{
public:
    virtual ~IKTFunction() = default;

    // Function identification
    virtual unsigned short GetFunctionMark() const = 0;
    virtual std::string GetFunctionName() const = 0;
    virtual std::string GetDescription() const = 0;
    
    // Parameter information
    virtual std::vector<std::string> GetParameterNames() const = 0;
    virtual std::vector<std::string> GetParameterDescriptions() const = 0;
    
    // Function pointer for C-style interface
    virtual pKTFUNC GetKTFunctionPointer() const = 0;
    
    // Validation and metadata
    virtual bool IsValid() const = 0;
    virtual std::string GetCategory() const = 0;
    virtual int GetMinInputCount() const = 0;
    virtual bool SupportsVariableInputs() const = 0;
    virtual int GetExpectedParameterCount() const = 0;
    virtual bool RequiresFinancialData() const = 0;
    virtual bool RequiresExtendedData() const = 0;
};

// Smart pointer type for KT functions
using KTFunctionPtr = std::shared_ptr<IKTFunction>;

// Forward declaration
class KTFunctionRegistry;

#endif // __IKT_FUNCTION_H__