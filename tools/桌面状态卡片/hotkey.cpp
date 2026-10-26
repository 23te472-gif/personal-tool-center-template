#define UNICODE
#define _UNICODE
#include <windows.h>
#include <shellapi.h>
#include <filesystem>
#include <fstream>
#include <string>

constexpr wchar_t CLASS[]=L"CodexStatusCardHotkeyAgent";
constexpr UINT TRAY=WM_APP+1,OPEN=WM_APP+2;
HINSTANCE instance;NOTIFYICONDATAW icon{};std::wstring directory;bool registered=false;
void openCard(){
    auto path=(std::filesystem::path(directory)/L"DesktopStatusCard.exe").wstring();
    std::wstring command=L"\""+path+L"\"";STARTUPINFOW start{sizeof(start)};PROCESS_INFORMATION process{};
    if(CreateProcessW(path.c_str(),command.data(),nullptr,nullptr,FALSE,0,nullptr,directory.c_str(),&start,&process)){
        CloseHandle(process.hThread);CloseHandle(process.hProcess);
    }else MessageBoxW(nullptr,L"状态卡片未能启动，请保留启动器与 DesktopStatusCard.exe 在同一目录。",L"桌面状态卡片",MB_OK|MB_ICONERROR);
}
void addTray(HWND hwnd){
    icon.cbSize=sizeof(icon);icon.hWnd=hwnd;icon.uID=1;icon.uFlags=NIF_ICON|NIF_TIP|NIF_MESSAGE;
    icon.uCallbackMessage=TRAY;icon.hIcon=LoadIconW(instance,MAKEINTRESOURCEW(1));
    wcscpy_s(icon.szTip,L"桌面状态卡片 · Ctrl+Alt+F9 打开");Shell_NotifyIconW(NIM_ADD,&icon);
}
LRESULT CALLBACK procedure(HWND hwnd,UINT message,WPARAM w,LPARAM l){
    static UINT taskbar=RegisterWindowMessageW(L"TaskbarCreated");
    if(message==taskbar){addTray(hwnd);return 0;}
    switch(message){
    case WM_CREATE:
        registered=RegisterHotKey(hwnd,1,MOD_CONTROL|MOD_ALT|MOD_NOREPEAT,VK_F9)!=FALSE;
        if(!registered){
            auto error=GetLastError();std::ofstream(std::filesystem::path(directory)/L"hotkey-error.txt")<<"RegisterHotKey Ctrl+Alt+F9 error="<<error;
            MessageBoxW(nullptr,L"Ctrl+Alt+F9 暂时无法注册，可能已被其他软件占用。状态卡片仍可从工具中心直接打开。",L"启动键未注册",MB_OK|MB_ICONWARNING);return -1;
        }
        addTray(hwnd);return 0;
    case WM_HOTKEY:case OPEN:openCard();return 0;
    case TRAY:
        if(l==WM_LBUTTONDBLCLK)openCard();
        else if(l==WM_RBUTTONUP){
            HMENU menu=CreatePopupMenu();AppendMenuW(menu,MF_STRING,1,L"打开状态卡片  Ctrl+Alt+F9");
            AppendMenuW(menu,MF_SEPARATOR,0,nullptr);AppendMenuW(menu,MF_STRING,2,L"退出快捷键启动器");
            POINT p;GetCursorPos(&p);SetForegroundWindow(hwnd);
            int result=TrackPopupMenu(menu,TPM_RETURNCMD|TPM_RIGHTBUTTON,p.x,p.y,0,hwnd,nullptr);DestroyMenu(menu);
            if(result==1)openCard();else if(result==2)DestroyWindow(hwnd);
            PostMessageW(hwnd,WM_NULL,0,0);
        }return 0;
    case WM_DESTROY:
        if(registered)UnregisterHotKey(hwnd,1);Shell_NotifyIconW(NIM_DELETE,&icon);PostQuitMessage(0);return 0;
    }
    return DefWindowProcW(hwnd,message,w,l);
}
int WINAPI wWinMain(HINSTANCE inst,HINSTANCE,LPWSTR,int){
    instance=inst;wchar_t file[32768];GetModuleFileNameW(nullptr,file,32768);directory=std::filesystem::path(file).parent_path().wstring();
    HANDLE mutex=CreateMutexW(nullptr,TRUE,L"Local\\CodexStatusCardHotkeyV1");if(!mutex)return 3;
    if(GetLastError()==ERROR_ALREADY_EXISTS){
        for(int i=0;i<20;++i){HWND old=FindWindowW(CLASS,L"桌面状态卡片快捷键");if(old){PostMessageW(old,OPEN,0,0);break;}Sleep(100);}
        CloseHandle(mutex);return 0;
    }
    WNDCLASSW wc{};wc.lpfnWndProc=procedure;wc.hInstance=inst;wc.lpszClassName=CLASS;RegisterClassW(&wc);
    // A hidden message window handles only hotkeys/tray clicks; no polling thread or performance collection.
    HWND hwnd=CreateWindowW(CLASS,L"桌面状态卡片快捷键",WS_OVERLAPPED,0,0,0,0,nullptr,nullptr,inst,nullptr);
    if(!hwnd){CloseHandle(mutex);return 2;}
    openCard();MSG msg{};while(GetMessageW(&msg,nullptr,0,0)>0){TranslateMessage(&msg);DispatchMessageW(&msg);}
    ReleaseMutex(mutex);CloseHandle(mutex);return 0;
}
