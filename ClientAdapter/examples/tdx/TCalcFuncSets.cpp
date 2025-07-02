#include "pch.h"
#include "TCalcFuncSets.h"

// export functions are defined in client_tdx.h
#include "client/client_tdx.h"
#include "client/client_tdx_magic.h"
//include "ta-lib\include\ta_libc.h"

#define __DLLVERSION__  "tdx 1.0.0"

#if 0
void TestPlugin1(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc)
{
	for (int i = 0; i < DataLen; i++)
		pfOUT[i] = (float)i;
}

void TestPlugin2(int DataLen, float* pfOUT, float* pfINa, float* pfINb, float* pfINc)
{
	//	char name[256] = "1234 Hello World";

#if 0
	for (int i = 0; i < DataLen; i++)
	{
		pfOUT[i] = pfINa[i] + pfINb[i] + pfINc[i];
		pfOUT[i] = pfOUT[i] / 3;
	}
#endif

	for (int i = 0; i < DataLen; i++)
	{
		pfOUT[i] = pfINa[i];
	}

}

void test_talib_ma(int DataLen,float* pfOUT,float* pfINa,float* pfINb,float* pfINc)
{
	TA_Real    closePrice[10000];
	TA_Real    out[10000];
	TA_Integer outBeg;
	TA_Integer outNbElement;

	unsigned int i;

	/* ... initialize your closing price here... */
	for( i=0;i<DataLen;i++)
	{
		closePrice[i] = pfINa[i];
	}

	TA_Integer retCode = TA_MA( 0, DataLen,
		&closePrice[0],
		30,TA_MAType_SMA,
		&outBeg, &outNbElement, &out[0] );

	/* The output is displayed here */
	for( i=0; i < outNbElement; i++ )
	{
		pfOUT[i+outBeg] = out[i];
		//printf( "Day %d = %f\n", outBeg+i, out[i] );
	}
}

#endif


PluginTCalcFuncInfo g_CalcFuncSets[] =
{
	//{1111,(pPluginFUNC)&TestPlugin1},
	//{2111,(pPluginFUNC)&TestPlugin2},

	//put funcid / funcname here
	REG_TDX_FUNCSETS(1,Tdx_API_1)
	REG_TDX_FUNCSETS(2,Tdx_API_2)
	REG_TDX_FUNCSETS(3,Tdx_API_3)
	REG_TDX_FUNCSETS(4,Tdx_API_4)
	REG_TDX_FUNCSETS(5,Tdx_API_5)

	REG_TDX_FUNCSETS(6,Tdx_API_6)
	REG_TDX_FUNCSETS(7,Tdx_API_7)
	REG_TDX_FUNCSETS(8,Tdx_API_8)
	REG_TDX_FUNCSETS(9,Tdx_API_9)
	REG_TDX_FUNCSETS(10,Tdx_API_10)

	REG_TDX_FUNCSETS(200,ConfigDaShu_part1)
	REG_TDX_FUNCSETS(201,ConfigDaShu_part2)
	REG_TDX_FUNCSETS(202,TDX_GetDaShu)
	REG_TDX_FUNCSETS(203,TDX_GetCircleNum)
	REG_TDX_FUNCSETS(204,TDX_GetCircleStartVal)
	REG_TDX_FUNCSETS(205,TDX__GetCircleNumAngle)
	REG_TDX_FUNCSETS(206,TDX_GetPrevNextCircleNum)
	REG_TDX_FUNCSETS(207,TDX_CheckBalanceV2)
	REG_TDX_FUNCSETS(208,TDX_CheckBalanceV2_series)
	REG_TDX_FUNCSETS(209,TDX_GetLuKas)
	REG_TDX_FUNCSETS(210,TDX_GetLuKasReverse)
};



BOOL RegisterTdxFunc(PluginTCalcFuncInfo** pFun)
{
	if(*pFun==NULL)
	{
		(*pFun)=g_CalcFuncSets;
		return TRUE;
	}
	return FALSE;
}
