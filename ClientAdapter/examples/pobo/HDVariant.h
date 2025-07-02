/*
class _hdvariant, 汇点指标计算模块通用数据类型,
用于统一处理单点数值与字符串类型，便于函数编写，
作者：小菜
日期：2010.11.24
*/

#ifndef _HD_VARIANT_CLASS__
#define _HD_VARIANT_CLASS__
#pragma warning( disable : 4996)

#include <windows.h>
#include <math.h>

#define MIN_EQUAL_STANDARD	1e-6

#pragma pack(push, 1)

enum DataType
{
	DT_NULL = 0,	//无效数据
//	DT_BOOL = 1,		
	DT_INT = 2,
//	DT_UINT = 3,
	DT_DOUBLE = 4,
	DT_STRING = 5,
	DT_POINTER = 6,		//void类型指针
};

class _hdvariant
{
public:
	struct HandleString
	{
		char *pStr;
		long *use;
	};

	unsigned char vType;
	union
	{
		int			iVal;
		double		dVal;
		HandleString	strVal;
		void*		pVoid;
	};
	
public:	
	_hdvariant() { vType = DT_NULL; dVal = 0; }
	_hdvariant(bool bval) {vType = DT_INT; iVal = bval ? 1 : 0;}
	_hdvariant(int ival) {vType = DT_INT; iVal = ival;}
	_hdvariant(UINT uval) {vType = DT_INT; iVal = (int)uval;}
	_hdvariant(double dval) {vType = DT_DOUBLE; dVal = dval;}
	_hdvariant(const char *pstr) 
	{
		if(pstr != NULL)
		{
			vType = DT_STRING;
			HandleString handle;
			handle.pStr = new char[strlen(pstr)+1];
			strcpy(handle.pStr, pstr);
			handle.use = new long(0);
			setstring(handle);
		}
		else
		{
			vType = DT_NULL;
			dVal = 0;
		}
	}
	_hdvariant(void *pvoid) {vType = DT_POINTER; pVoid = pvoid;}
	_hdvariant(const _hdvariant& val)
	{
		vType = val.vType;
		if(DT_STRING == vType)
			setstring(val.strVal);
		else
			dVal = val.dVal;
	}
	
	void setstring(const HandleString& handle)
	{
		::InterlockedIncrement( handle.use );
		strVal.pStr = handle.pStr;
		strVal.use = handle.use;
	}
	void freestring()
	{
		if(DT_STRING == vType && ::InterlockedDecrement( strVal.use ) == 0)
		{
			delete []strVal.pStr;
			delete strVal.use;
		}
	}

	~_hdvariant(){ freestring(); }

	void Clear() {freestring();vType = DT_NULL;}

	_hdvariant& operator = (bool bval) {freestring();vType = DT_INT; iVal = bval ? 1 : 0; return *this;}
	_hdvariant& operator = (int ival) {freestring();vType = DT_INT; iVal = ival; return *this;}
	_hdvariant& operator = (UINT uval) {freestring();vType = DT_INT; iVal = (int)uval; return *this;}
	_hdvariant& operator = (double dval) {freestring();vType = DT_DOUBLE;dVal = dval;return *this;}
	_hdvariant& operator = (const char *pstr)
	{
		freestring();
		if(pstr != NULL)
		{
			vType = DT_STRING;
			HandleString handle;
			handle.pStr = new char[strlen(pstr)+1];
			strcpy(handle.pStr, pstr);
			handle.use = new long(0);
			setstring(handle);
		}
		else
		{
			vType = DT_NULL;
			dVal = 0;
		}
		return *this;
	}
	_hdvariant& operator = (void *pvoid) {freestring();vType = DT_POINTER; pVoid = pvoid; return *this;}
	_hdvariant& operator = (const _hdvariant& val)
	{
		freestring();
		vType = val.vType;
		if(DT_STRING == vType)
			setstring(val.strVal);
		else
			dVal = val.dVal;
		return *this;
	}
	
	inline _hdvariant operator - ();		//相反数

	_hdvariant operator + (const _hdvariant& val) {return AddH(val);}
	_hdvariant operator - (const _hdvariant& val) {return SubstractH(val);}
	_hdvariant operator * (const _hdvariant& val) {return MultiplyH(val);}
	_hdvariant operator / (const _hdvariant& val) {return DevideH(val);}	
	bool operator == (const _hdvariant& val) {return EqualtoH(val);}
	bool operator != (const _hdvariant& val) {return UnEqualtoH(val);}
	bool operator > (const _hdvariant& val) {return LargerthanH(val);}
	bool operator >= (const _hdvariant& val) {return LargerEqualH(val);}
	bool operator < (const _hdvariant& val) {return LessthanH(val);}
	bool operator <= (const _hdvariant& val) {return LessEqualH(val);}
	
	_hdvariant operator + (_hdvariant& val) {return AddH(val);}
	_hdvariant operator - (_hdvariant& val) {return SubstractH(val);}
	_hdvariant operator * (_hdvariant& val) {return MultiplyH(val);}
	_hdvariant operator / (_hdvariant& val) {return DevideH(val);}	
	bool operator == (_hdvariant& val) {return EqualtoH(val);}
	bool operator != (_hdvariant& val) {return UnEqualtoH(val);}
	bool operator > (_hdvariant& val) {return LargerthanH(val);}
	bool operator >= (_hdvariant& val) {return LargerEqualH(val);}
	bool operator < (_hdvariant& val) {return LessthanH(val);}
	bool operator <= (_hdvariant& val) {return LessEqualH(val);}
	
	template<class T>
		_hdvariant operator + (T val) {return Add((double)val);}
	template<class T>
		_hdvariant operator - (T val) {return Substract((double)val);}
	template<class T>
		_hdvariant operator * (T val) {return Multiply((double)val);}
	template<class T>
		_hdvariant operator / (T val) {return Devide((double)val);}
	template<class T>
		bool operator == (T val) {return Equalto((double)val);}
	template<class T>
		bool operator != (T val) {return UnEqualto((double)val);}
	template<class T>
		bool operator > (T val) {return Largerthan((double)val);}
	template<class T>
		bool operator >= (T val) {return LargerEqual((double)val);}
	template<class T>
		bool operator < (T val) {return Lessthan((double)val);}
	template<class T>
		bool operator <= (T val) {return LessEqual((double)val);}
	
	inline operator bool();
	inline operator int();
	inline operator UINT();
	inline operator double();
	inline operator char*();
	inline operator void*();
	
	inline operator bool() const;
	inline operator int() const;
	inline operator UINT() const;
	inline operator double() const;
	inline operator char*() const;
	inline operator void*() const;
	
protected:			
	inline _hdvariant AddH(const _hdvariant& val);
	inline _hdvariant SubstractH(const _hdvariant& val);
	inline _hdvariant MultiplyH(const _hdvariant& val);
	inline _hdvariant DevideH(const _hdvariant& val);
	
	inline bool EqualtoH(const _hdvariant& val);
	inline bool UnEqualtoH(const _hdvariant& val);
	inline bool LargerthanH(const _hdvariant& val);
	inline bool LargerEqualH(const _hdvariant& val);
	inline bool LessthanH(const _hdvariant& val);
	inline bool LessEqualH(const _hdvariant& val);
	//以下模板函数限定内部使用，可以保证不会传入非数值的类型，
	//因此不需再下列运算操作中考虑指针等异常类型
	_hdvariant Add(double val)
	{
		if(vType == DT_DOUBLE)
			return (dVal + val);
		if(vType == DT_INT)
			return (iVal + val);
		
		return _hdvariant();
	}
	
	_hdvariant Substract(double val)
	{
		if(vType == DT_DOUBLE)
			return (dVal - val);
		if(vType == DT_INT)
			return (iVal - val);
		
		return _hdvariant();
	}
	
	_hdvariant Multiply(double val)
	{
		if(vType == DT_DOUBLE)
			return (dVal * val);
		if(vType == DT_INT)
			return (iVal * val);
		
		return _hdvariant();
	}
	
	_hdvariant Devide(double val)
	{
		if(val > MIN_EQUAL_STANDARD || val < -MIN_EQUAL_STANDARD)
		{
			if(vType == DT_DOUBLE)
				return (dVal / val);
			if(vType == DT_INT)
				return (iVal / val);
		}
		
		return _hdvariant();
	}
	
	bool Equalto(double val)
	{
		if(vType == DT_DOUBLE)
			return (dVal - val) < MIN_EQUAL_STANDARD && (dVal - val) > -MIN_EQUAL_STANDARD;
		if(vType == DT_INT)
			return (iVal - val) < MIN_EQUAL_STANDARD && (iVal - val) > -MIN_EQUAL_STANDARD;
		
		return false;
	}
	
	bool UnEqualto(double val)
	{
		if(vType == DT_DOUBLE)
			return (dVal - val) >= MIN_EQUAL_STANDARD || (dVal - val) <= -MIN_EQUAL_STANDARD;
		if(vType == DT_INT)
			return (iVal - val) >= MIN_EQUAL_STANDARD || (iVal - val) <= -MIN_EQUAL_STANDARD;
		
		return false;
	}
	
	bool Largerthan(double val)
	{
		if(vType == DT_DOUBLE)
			return (dVal - val) >= MIN_EQUAL_STANDARD;
		if(vType == DT_INT)
			return (iVal - val) >= MIN_EQUAL_STANDARD;
		
		return false;
	}
	
	bool LargerEqual(double val)
	{
		if(vType == DT_DOUBLE)
			return (dVal - val) > -MIN_EQUAL_STANDARD;
		if(vType == DT_INT)
			return (iVal - val) > -MIN_EQUAL_STANDARD;
		
		return false;
	}
	
	bool Lessthan(double val)
	{
		if(vType == DT_DOUBLE)
			return (dVal - val) <= -MIN_EQUAL_STANDARD;
		if(vType == DT_INT)
			return (iVal - val) <= -MIN_EQUAL_STANDARD;
		
		return false;
	}
	
	bool LessEqual(double val)
	{
		if(vType == DT_DOUBLE)
			return (dVal - val) < MIN_EQUAL_STANDARD;
		if(vType == DT_INT)
			return (iVal - val) < MIN_EQUAL_STANDARD;
		
		return false;
	}
	
};

typedef _hdvariant HDVARIANT;

_hdvariant _hdvariant::operator -()
{
	if(vType == DT_DOUBLE)
		return -dVal;
	if(vType == DT_INT)
		return -iVal;

	return _hdvariant();
}

_hdvariant _hdvariant::AddH(const _hdvariant& val)
{
	if(val.vType == DT_DOUBLE)
		return Add(val.dVal);
	if(val.vType == DT_INT)
		return Add(val.iVal);
	
	return _hdvariant();
}

_hdvariant _hdvariant::SubstractH(const _hdvariant& val)
{
	if(val.vType == DT_DOUBLE)
		return Substract(val.dVal);
	if(val.vType == DT_INT)
		return Substract(val.iVal);
	
	return _hdvariant();
}

_hdvariant _hdvariant::MultiplyH(const _hdvariant& val)
{
	if(val.vType == DT_DOUBLE)
		return Multiply(val.dVal);
	if(val.vType == DT_INT)
		return Multiply(val.iVal);
	
	return _hdvariant();
}

_hdvariant _hdvariant::DevideH(const _hdvariant& val)
{
	if(val.vType == DT_DOUBLE)
		return Devide(val.dVal);
	if(val.vType == DT_INT)
		return Devide(val.iVal);
	
	return _hdvariant();
}

bool _hdvariant::EqualtoH(const _hdvariant& val)
{
	switch(val.vType)
	{
	case DT_INT:
		return Equalto(val.iVal);
	case DT_DOUBLE:
		return Equalto(val.dVal);
	case DT_STRING:
		if(DT_STRING == this->vType)
			return strcmp(strVal.pStr, val.strVal.pStr) == 0;
		break;
	case DT_POINTER:
		if(DT_POINTER == this->vType)
			return (UINT)this->pVoid == (UINT)val.pVoid;
		break;
	case DT_NULL:
		if(DT_NULL == vType)
			return true;
	default:
		break;
	}
	
	return false;
}

bool _hdvariant::UnEqualtoH(const _hdvariant& val)
{
	switch(val.vType)
	{
	case DT_INT:
		return UnEqualto(val.iVal);
	case DT_DOUBLE:
		return UnEqualto(val.dVal);
	case DT_STRING:
		if(DT_STRING == this->vType)
			return strcmp(strVal.pStr, val.strVal.pStr) != 0;
		break;
	case DT_POINTER:
		if(DT_POINTER == this->vType)
			return (UINT)this->pVoid != (UINT)val.pVoid;
		break;
	case DT_NULL:
		if(DT_NULL != vType)
			return true;
	default:
		break;
	}
	
	return false;
}

bool _hdvariant::LargerthanH(const _hdvariant& val)
{
	if(val.vType == DT_DOUBLE)
		return Largerthan(val.dVal);
	if(val.vType == DT_INT)
		return Largerthan(val.iVal);
	if(val.vType == DT_STRING && DT_STRING == this->vType)
		return strcmp(strVal.pStr, val.strVal.pStr) > 0;
	
	return false;
}

bool _hdvariant::LargerEqualH(const _hdvariant& val)
{
	if(val.vType == DT_DOUBLE)
		return LargerEqual(val.dVal);
	if(val.vType == DT_INT)
		return LargerEqual(val.iVal);
	if(val.vType == DT_STRING && DT_STRING == this->vType)
		return strcmp(strVal.pStr, val.strVal.pStr) >= 0;
	
	return false;
}

bool _hdvariant::LessthanH(const _hdvariant& val)
{
	if(val.vType == DT_DOUBLE)
		return Lessthan(val.dVal);
	if(val.vType == DT_INT)
		return Lessthan(val.iVal);
	if(val.vType == DT_STRING && DT_STRING == this->vType)
		return strcmp(strVal.pStr, val.strVal.pStr) < 0;
	
	return false;
}

bool _hdvariant::LessEqualH(const _hdvariant& val)
{
	if(val.vType == DT_DOUBLE)
		return LessEqual(val.dVal);
	if(val.vType == DT_INT)
		return LessEqual(val.iVal);
	if(val.vType == DT_STRING && DT_STRING == this->vType)
		return strcmp(strVal.pStr, val.strVal.pStr) <= 0;
	
	return false;
}

//////////////////////////
_hdvariant::operator bool()
{
	if(vType == DT_INT)
		return (iVal != 0);
	if(vType == DT_DOUBLE)
		return (dVal>=MIN_EQUAL_STANDARD || dVal<=-MIN_EQUAL_STANDARD);	

	return false;
}

_hdvariant::operator int()
{
	if(vType == DT_INT)
		return iVal;
	if(vType == DT_DOUBLE)
		return (int)(dVal + 0.5);
	
	return 0;
}

_hdvariant::operator UINT()
{
	if(vType == DT_INT)
		return (UINT)iVal;
	
	return (UINT)(-1);
}

_hdvariant::operator double()
{
	if(vType == DT_DOUBLE)
		return dVal;
	if(vType == DT_INT)
		return iVal;
	
	return 0.0;
}

_hdvariant::operator char*()
{
	if(vType == DT_STRING)
		return strVal.pStr;

	char a[1] = { "" };
	return a;
}

_hdvariant::operator void*()
{
	if(vType == DT_POINTER)
		return pVoid;

	return NULL;
}

_hdvariant::operator bool() const
{
	if(vType == DT_INT)
		return (iVal != 0);
	if(vType == DT_DOUBLE)
		return (dVal>=MIN_EQUAL_STANDARD || dVal<=-MIN_EQUAL_STANDARD);	

	return false;
}

_hdvariant::operator int() const
{
	if(vType == DT_INT)
		return iVal;
	if(vType == DT_DOUBLE)
		return (int)(dVal + 0.5);
	
	return 0;
}

_hdvariant::operator UINT() const
{
	if(vType == DT_INT)
		return (UINT)iVal;
	
	return (UINT)(-1);
}

_hdvariant::operator double() const
{
	if(vType == DT_DOUBLE)
		return dVal;
	if(vType == DT_INT)
		return iVal;
	
	return 0.0;
}

_hdvariant::operator char*() const
{
	if(vType == DT_STRING)
		return strVal.pStr;

	char a[1] = { "" };
	return a;
}

_hdvariant::operator void*() const
{
	if(vType == DT_POINTER)
		return pVoid;

	return NULL;
}

#pragma pack(pop)

#endif