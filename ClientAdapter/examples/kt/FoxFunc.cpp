// FoxFunc.cpp : Defines the entry point for the DLL application.
//

#include "pch.h"
#include "FoxFunc.h"
#include <limits>
//计算收盘价的均价,一个常数参数,表示计算周期
//调用方法:
//	"FOXFUNC@MYMACLOSE"(5)

extern "C" __declspec(dllexport) int WINAPI MYMACLOSE(CALCINFO* pData)
{
	if ( pData->m_pfParam1 &&				//参数1有效
		 pData->m_nParam1Start<0 &&			//参数1为常数
		 pData->m_pfParam2==NULL )			//仅有一个参数
	{
		float fParam = *pData->m_pfParam1;
		int nPeriod = (int)fParam;			//参数1
		if(nPeriod>0)
		{
			float fTotal;
			int i, j;
			for ( i = nPeriod-1; i < pData->m_nNumData; i++ )//计算nPeriod周期的均线,数据从nPeriod-1开始有效
			{
				fTotal = 0.0f;
				for ( j = 0; j < nPeriod; j++ )				//累加
					fTotal += pData->m_pData[i-j-1].m_fClose;
				pData->m_pResultBuf[i] = fTotal/nPeriod;	//平均
			}
			return nPeriod-1;
		}
	}
	return -1;
}

//计算均价,2个参数,参数1为待求均线的数据,参数2表示计算周期
//调用方法:
//	"FOXFUNC@MYMAVAR"(CLOSE-OPEN,5)

extern "C"  __declspec(dllexport) int WINAPI MYMAVAR(CALCINFO* pData)
{
	if(pData->m_pfParam1 && pData->m_pfParam2 && 	//参数1,2有效
		pData->m_nParam1Start>=0 &&					//参数1为序列数
		pData->m_pfParam3==NULL)					//有2个参数
	{
		const float*  pValue = pData->m_pfParam1;	//参数1
		int nFirst = pData->m_nParam1Start;			//有效值起始位
		float fParam = *pData->m_pfParam2;			//参数2
		int nPeriod = (int)fParam;			

		if( nFirst >= 0 && nPeriod > 0 )
		{
			float fTotal;
			int i, j;
			for ( i = nFirst+nPeriod-1; i < pData->m_nNumData; i++ )
			{
				fTotal = 0.0f;
				for ( j=0; j < nPeriod; j++ )			//累加
					fTotal += pValue[i-j];
				pData->m_pResultBuf[i] = fTotal/nPeriod;//平均
			}
			return nFirst+nPeriod-1;
		}
		
	}
	return -1;
}

//计算多个序列的均值,5个参数,参数1-4为待求多个序列,参数5用于举例说明数值参数的用法，实际在此例中无需该参数
/*
调用方法:
	MA1:=MA(CLOSE,3);
	MA2:=MA(CLOSE,6);
	MA3:=MA(CLOSE,12);
	MA4:=MA(CLOSE,24);
	MYBBI: "FOXFUNC@MYBBI"(MA1, MA2, MA3, MA4, 4);
*/

extern "C"  __declspec(dllexport) int WINAPI MYBBI(CALCINFO* pData)
{
	if ( pData->m_pCalcParam[0].m_nParamStart >= 0 &&
		 pData->m_pCalcParam[1].m_nParamStart >= 0 &&
		 pData->m_pCalcParam[2].m_nParamStart >= 0 &&
		 pData->m_pCalcParam[3].m_nParamStart >= 0 )			//4个序列都含有效数值
	{
		//计算返回的序列的第一个有效值位置
		int nFirst = pData->m_pCalcParam[3].m_nParamStart;		//已知返回的序列的第一个有效值位置与第4个序列一致
//若不知，则
/*
		int nFirst = pData->m_pCalcParam[0].m_nParamStart;
		if ( nFirst < pData->m_pCalcParam[1].m_nParamStart ) 
			nFirst = pData->m_pCalcParam[1].m_nParamStart;
		if ( nFirst < pData->m_pCalcParam[2].m_nParamStart ) 
			nFirst = pData->m_pCalcParam[2].m_nParamStart;
		if ( nFirst < pData->m_pCalcParam[3].m_nParamStart ) 
			nFirst = pData->m_pCalcParam[3].m_nParamStart;
 */

		const float* pValue1 = pData->m_pCalcParam[0].m_pfParam;
		const float* pValue2 = pData->m_pCalcParam[1].m_pfParam;
		const float* pValue3 = pData->m_pCalcParam[2].m_pfParam;
		const float* pValue4 = pData->m_pCalcParam[3].m_pfParam;
		int nNum = (int)(pData->m_pCalcParam[4].m_fParam);		//实际上该例中已知nNum=4，在此用于说明数值参数的用法
		for( int i = nFirst; i < pData->m_nNumData; i++ )
		{
			pData->m_pResultBuf[i] = 
				(pValue1[i] + pValue2[i] + pValue3[i] + pValue4[i])/nNum;
		}
		return nFirst;
	}
	return -1;
}

extern "C" __declspec(dllexport) int WINAPI FUCK(CALCINFO* pData)
{
	for(int i=0; i<pData->m_nNumData; i++)
		pData->m_pResultBuf[i] = (float)i;
	return 0;
}

extern "C" __declspec(dllexport) int WINAPI mymax(CALCINFO* pData)
{
	float max_value = 0.0f;
	if (pData->m_nNumParam == 1)
	{
		max_value = pData->m_pCalcParam[0].m_fParam;
	}
	else if (pData->m_nNumParam > 1)
	{
		max_value = pData->m_pCalcParam[0].m_fParam;
		for(int i = 1; i < pData->m_nNumParam; i++)
		{
			const float this_value = pData->m_pCalcParam[i].m_fParam;
			if (this_value > max_value)
			{
				max_value = this_value;
			}
		}
	}




	for(int i = 0; i < pData->m_nNumData; i++)
	{
		pData->m_pResultBuf[i] = max_value;
	}
	
	return 0;
}

//################### 以下这些例子只适用于逐根模式
#define INVALID_NUMERIC std::numeric_limits<double>::quiet_NaN()
/** dll里实现ma, 计算结果和公式里调用ma一样
使用， 在公式里声明就可使用
extern 'FoxFunc.dll'  void  my_ma(NumericSeries resultArray, NumericSeries array, int n, int barpos);
resultArray 存放结果的序列
array 要计算ma的序列
n 要计算几周期的ma
barpos 当前运算的第几根k线，从1开始
*/
extern "C" __declspec(dllexport) void WINAPI my_ma(double* resultArray, double* array, int n, int barpos)
{	
	int nK = barpos - 1;
	if(barpos >= n)
	{
		double sum=0;
		for(int i = 0; i < n; i++)
			sum += array[nK-i];
		resultArray[nK] = sum / n;
	}
	else
	{
		resultArray[nK] = INVALID_NUMERIC;
	}
	
}

// ArrayAddSub 展示了传入序列并修改序列的值
// 分别把array1和array2加减一个数值
extern "C" __declspec(dllexport) double WINAPI ArrayAddSub(double* array1, double* array2, int i, double add)
{
	array1[i-1] = array1[i-1]  + add;
	array2[i-1] = array2[i-1]  - add;
	return 1;
}

// 可以传递各种C或者windows基本类型作为参数和返回值
extern "C" __declspec(dllexport) double WINAPI ALL_TYPE_ADD(char d1,  int d2, LONG d3, DWORD d4, float d5, double d6, BOOL d7, ULONG d8)
{
	double sum = d1 +  d2 +   d3 +   d4 +   d5 +   d6 +   d7 +   d8;
	return sum;
}

// 传递引用
extern "C"  __declspec(dllexport) void WINAPI TestNumbericRef(double* x, double* y, double* z)
{
	*x = 6;
	*y = 7;
	*z = 8;
}

// 传入字符串
extern "C"  __declspec(dllexport) void WINAPI SetString(LPCWSTR str1, LPCWSTR str2)
{
	
}

// 传回字符串
extern "C"  __declspec(dllexport) LPCWSTR WINAPI MyString()
{
	return L"MyString测试";
}

//甚至传回指针
extern "C"  __declspec(dllexport) double* WINAPI NewDouble()
{
	double* p = new double[10000];
	return p;
}
// 释放NewDouble里建立的指针
extern "C"  __declspec(dllexport) void WINAPI FreeDouble(double* p)
{
	delete []p;
}


