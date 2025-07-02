#ifndef __TCALC_FUNC_SETS
#define __TCALC_FUNC_SETS
#include "PluginTCalcFunc.h"



extern PluginTCalcFuncInfo g_CalcFuncSets[];

//函数(数据个数,输出,输入a,输入b,输入c)
typedef void(*pPluginFUNC)(int, float*, float*, float*, float*);

#define REG_TDX_FUNCSETS(funcid,pFunc) {funcid,(pPluginFUNC)&pFunc},

#ifdef __cplusplus
extern "C"
{
#endif //__cplusplus
	__declspec(dllexport) BOOL RegisterTdxFunc(PluginTCalcFuncInfo** pFun);
#ifdef __cplusplus
}
#endif //__cplusplus


#endif //__TCALC_FUNC_SETS