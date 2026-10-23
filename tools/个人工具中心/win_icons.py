"""Read a small shell icon into pixels, releasing all native handles."""
import ctypes
from ctypes import wintypes as W
from pathlib import Path
import os

def shortcut_image(item,size=72):
    """Read an explicit ICO directly, independent of Shell's shortcut cache."""
    from PIL import Image
    value=item.get('icon','')
    source,separator,index=value.rpartition(',')
    if not separator:source=value;index='0'
    path=Path(os.path.expandvars(source.strip().strip('"')))
    if index.strip()=='0' and path.suffix.lower()=='.ico' and path.is_file():
        try:
            with Image.open(path) as image:
                if (size,size) in image.ico.sizes():image=image.ico.getimage((size,size))
                result=image.convert('RGBA');result.thumbnail((size,size),Image.Resampling.LANCZOS)
                canvas=Image.new('RGBA',(size,size))
                canvas.alpha_composite(result,((size-result.width)//2,(size-result.height)//2))
                return canvas
        except (OSError,ValueError):pass
    return shell_image(item['path'],size)

def shell_image(path,size=72):
    from PIL import Image
    class Info(ctypes.Structure):
        _fields_=[('icon',W.HICON),('index',ctypes.c_int),('attributes',W.DWORD),('display',W.WCHAR*260),('type',W.WCHAR*80)]
    class Header(ctypes.Structure):
        _fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bits',W.WORD),('compression',W.DWORD),('image_size',W.DWORD),('x',W.LONG),('y',W.LONG),('used',W.DWORD),('important',W.DWORD)]
    class Bitmap(ctypes.Structure):_fields_=[('header',Header),('colors',W.DWORD*3)]
    shell=ctypes.windll.shell32;user=ctypes.windll.user32;gdi=ctypes.windll.gdi32
    shell.SHGetFileInfoW.argtypes=[W.LPCWSTR,W.DWORD,ctypes.POINTER(Info),W.UINT,W.UINT];shell.SHGetFileInfoW.restype=ctypes.c_size_t
    user.GetDC.argtypes=[W.HWND];user.GetDC.restype=W.HDC
    user.ReleaseDC.argtypes=[W.HWND,W.HDC];user.DestroyIcon.argtypes=[W.HICON]
    gdi.CreateCompatibleDC.argtypes=[W.HDC];gdi.CreateCompatibleDC.restype=W.HDC
    gdi.CreateDIBSection.argtypes=[W.HDC,ctypes.POINTER(Bitmap),W.UINT,ctypes.POINTER(ctypes.c_void_p),W.HANDLE,W.DWORD];gdi.CreateDIBSection.restype=W.HBITMAP
    gdi.SelectObject.argtypes=[W.HDC,W.HANDLE];gdi.SelectObject.restype=W.HANDLE
    gdi.DeleteObject.argtypes=[W.HANDLE];gdi.DeleteDC.argtypes=[W.HDC]
    user.DrawIconEx.argtypes=[W.HDC,ctypes.c_int,ctypes.c_int,W.HICON,ctypes.c_int,ctypes.c_int,W.UINT,W.HBRUSH,W.UINT]
    info=Info()
    if not shell.SHGetFileInfoW(str(path),0,ctypes.byref(info),ctypes.sizeof(info),0x100):return None
    screen=None;dc=None;bitmap=None;old=None
    try:
        screen=user.GetDC(None);dc=gdi.CreateCompatibleDC(screen)
        details=Bitmap();details.header=Header(ctypes.sizeof(Header),size,-size,1,32,0,0,0,0,0,0);pixels=ctypes.c_void_p()
        bitmap=gdi.CreateDIBSection(dc,ctypes.byref(details),0,ctypes.byref(pixels),None,0)
        if not bitmap or not pixels.value:return None
        old=gdi.SelectObject(dc,bitmap);ctypes.memset(pixels,0,size*size*4)
        if not user.DrawIconEx(dc,0,0,info.icon,size,size,0,None,3):return None
        image=Image.frombytes('RGBA',(size,size),ctypes.string_at(pixels,size*size*4),'raw','BGRA')
        if image.getchannel('A').getextrema()==(0,0):image.putalpha(255)
        return image
    finally:
        if old:gdi.SelectObject(dc,old)
        if bitmap:gdi.DeleteObject(bitmap)
        if dc:gdi.DeleteDC(dc)
        if screen:user.ReleaseDC(None,screen)
        if info.icon:user.DestroyIcon(info.icon)
