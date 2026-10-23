"""Check the actual Shell shortcut icon handler, rather than only WScript properties."""
import ctypes,uuid
from ctypes import wintypes as W

class GUID(ctypes.Structure):
    _fields_=[('data',ctypes.c_byte*16)]
    @classmethod
    def parse(cls,value):return cls.from_buffer_copy(uuid.UUID(value).bytes_le)

def icon_location(path):
    ole=ctypes.WinDLL('ole32');ole.CoInitializeEx.argtypes=[ctypes.c_void_p,W.DWORD];ole.CoInitializeEx.restype=ctypes.c_long
    ole.CoCreateInstance.argtypes=[ctypes.POINTER(GUID),ctypes.c_void_p,W.DWORD,ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)];ole.CoCreateInstance.restype=ctypes.c_long
    initialized=ole.CoInitializeEx(None,2);pointers=[]
    def invoke(ptr,n,types,*values):
        table=ctypes.cast(ptr,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        return ctypes.WINFUNCTYPE(ctypes.c_long,ctypes.c_void_p,*types)(table[n])(ptr,*values)
    def check(hr):
        if hr!=0:raise OSError('Windows 不能提取快捷方式图标（0x%08X）；未标记为应用成功。'%(hr&0xffffffff))
    def query(ptr,iid):
        result=ctypes.c_void_p();check(invoke(ptr,0,[ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(GUID.parse(iid)),ctypes.byref(result)))
        pointers.append(result);return result
    try:
        link=ctypes.c_void_p()
        check(ole.CoCreateInstance(ctypes.byref(GUID.parse('00021401-0000-0000-C000-000000000046')),None,1,ctypes.byref(GUID.parse('000214F9-0000-0000-C000-000000000046')),ctypes.byref(link)))
        pointers.append(link)
        persist=query(link,'0000010b-0000-0000-C000-000000000046')
        check(invoke(persist,5,[W.LPCWSTR,W.DWORD],str(path),0))
        extractor=query(link,'000214fa-0000-0000-C000-000000000046')
        text=ctypes.create_unicode_buffer(1024);index=ctypes.c_int();flags=W.UINT()
        check(invoke(extractor,3,[W.UINT,W.LPWSTR,W.UINT,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(W.UINT)],2,text,1024,ctypes.byref(index),ctypes.byref(flags)))
        return dict(path=text.value,index=index.value,flags=flags.value)
    finally:
        for pointer in reversed(pointers):invoke(pointer,2,[])
        if initialized in (0,1):ole.CoUninitialize()
