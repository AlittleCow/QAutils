#ifndef __HD_DLLFUNC_INTERFACE_HH_
#define __HD_DLLFUNC_INTERFACE_HH_

#include "HDVariant.h"

#pragma pack(push, 1)
typedef struct tag_NTime
{
	unsigned short year;
	unsigned char month;
	unsigned char day;
	unsigned char hour;
	unsigned char minute;
	unsigned char second;
}NTime;

typedef struct tag_HISDAT
{
	NTime Time;			//时间
	BYTE  Null;			//非0表示无效值
	int	   Serial;		//偏移量
	double Open;		//开盘价
	double High;		//最高价
	double Low;			//最低价
	double Close;		//收盘价
	double Volume;		//成交量
	double Amount;		//持仓量
	double TurnOver;	//成交金额
	union
	{
		struct
		{
			WORD Raise;		//上涨家数
			WORD Down;		//下跌家数
		};
        DWORD   TotalTick;	//总笔数
		double	Settle;		//结算价
		double  Accrual;	//债券利息
	};
	double Buyvol;		//外盘
	double Sellvol;		//内盘

}HISDAT,*LPHISDAT;
#pragma pack(pop)

typedef struct tag_InputInfo
{
	UINT uSize;			//结构体大小
	UINT uVersion;		//版本号，210
	WORD wMarket;		//市场id
	char Code[32];		//股票、合约代码
	UINT uDate;			//走势日期
	WORD wPeriod;		//分析周期
	HWND hWnd;			//父窗口
	UINT uDataSize;		//数据个数
	LPHISDAT pHisData;	//基本历史数据
	void *pReserved1;	//预留指针1
	void *pReserved2;	//预留指针2
	void *pReserved3;	//预留指针3
	int nParam;			//参数个数,最多16个
	HDVARIANT* ParaValue[16];		//参数值，指针指向的数据，根据预先定义的参数类型分配单值或uDataSize个数的数组
	HDVARIANT* RetValue;	//函数返回结果,RT_VOID类型指针为NULL，
							//否则根据返回类型，指针指向的内存由外部申请好的单个HDVARIANT或HDVARIANT数组	
} INPUT_INFO;

typedef void (*HDDFCALL)(INPUT_INFO info);

#endif