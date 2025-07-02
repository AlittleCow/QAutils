
// The following ifdef block is the standard way of creating macros which make exporting 
// from a DLL simpler. All files within this DLL are compiled with the FUNCDLL_EXPORTS
// symbol defined on the command line. this symbol should not be defined on any project
// that uses this DLL. This way any other project whose source files include this file see 
// FUNCDLL_API functions as being imported from a DLL, wheras this DLL sees symbols
// defined with this macro as being exported.

#ifdef FUNCDLL_EXPORTS
#define FUNCDLL_API __declspec(dllexport)
#else
#define FUNCDLL_API __declspec(dllimport)
#endif

#include "DllFuncInterface.h"

extern "C" FUNCDLL_API void MYMA(INPUT_INFO info);
extern "C" FUNCDLL_API void MYSUM(INPUT_INFO info);
extern "C" FUNCDLL_API unsigned char HDDllAuthorize(const char *szMethod);

