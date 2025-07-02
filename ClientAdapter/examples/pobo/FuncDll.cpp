// FuncDll.cpp : Defines the entry point for the DLL application.
//

#include "stdafx.h"
#include "FuncDll.h"

BOOL APIENTRY DllMain( HANDLE hModule, 
                       DWORD  ul_reason_for_call, 
                       LPVOID lpReserved
					 )
{
    switch (ul_reason_for_call)
	{
		case DLL_PROCESS_ATTACH:
		case DLL_THREAD_ATTACH:
		case DLL_THREAD_DETACH:
		case DLL_PROCESS_DETACH:
			break;
    }
    return TRUE;
}


// This is an example of an exported function.
void MYMA(INPUT_INFO info)
{
	if(info.uSize != sizeof(INPUT_INFO) || info.uVersion != 210 || info.nParam != 2)
		return;
	int n = *(info.ParaValue[1]);
	if(n <= 0)
		return;
	
		double sum = 0;
		
		//查找第一个  有效值 
		int   nFirstValue = 0;
		BOOL  bExcute = FALSE ;
		for ( int i=0; i < info.uDataSize; i++)
		{
			if(DT_NULL != info.ParaValue[0]->vType)   //
			{
				nFirstValue = i;
				bExcute =TRUE;
			}	
			if( bExcute )
			{
				for ( i=nFirstValue; i < info.uDataSize; i++)
				{
					sum += (double)(info.ParaValue[0][i]);
					if ( i-nFirstValue < n-1 )	
						continue;
					
					info.RetValue[i]=sum/n;
					sum -= (double)info.ParaValue[0][i-n+1];
				}
				
				break ;
			}
		}
}

void MYSUM(INPUT_INFO info)
{
	if(info.nParam != 2)
		return;
	int n = *(info.ParaValue[1]);
	if(n <= 0)
		return;
	
	double sum = 0;
	
	//查找第一个  有效值 
	int   nFirstValue = 0;
	BOOL  bExcute = FALSE ;
	for ( int i=0; i < info.uDataSize; i++)
	{
		if(DT_NULL != info.ParaValue[0]->vType)   //
		{
			nFirstValue = i;
			bExcute =TRUE;
		}	
		if( bExcute )
		{
			for ( i=nFirstValue; i < info.uDataSize; i++)
			{
				sum += (double)(info.ParaValue[0][i]);
				if ( i-nFirstValue < n-1 )	
					continue;
				
				info.RetValue[i]=sum;
				sum -= (double)info.ParaValue[0][i-n+1];
			}
			
			break ;
		}
	}
}

unsigned char HDDllAuthorize(const char *szMethod)
{
 	if(strcmp(szMethod, "MYMA") == 0)
 		return 2;
	return 0;
}