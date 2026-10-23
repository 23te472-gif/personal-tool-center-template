#define NOMINMAX
#include <winsock2.h>
#include <ws2ipdef.h>
#include <windows.h>
#include <windowsx.h>
#include <iphlpapi.h>
#include <netioapi.h>
#include <psapi.h>
#include <shellapi.h>
#include <gdiplus.h>
#include <dwmapi.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <cstdio>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <map>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>
#include "metrics.hpp"

using namespace Gdiplus;
using Clock=std::chrono::steady_clock;
constexpr wchar_t CLASSNAME[]=L"CodexDesktopStatusCardNative";
constexpr wchar_t TITLE[]=L"桌面状态卡片";
constexpr UINT SAMPLE=WM_APP+1;
struct Disk {std::wstring name;uint64_t free=0,total=0;};
struct Adapter {ULONG id=0;std::wstring name;uint64_t rx=0,tx=0,link=0;};
struct Snapshot {
    double cpu=-1,down=0,up=0;bool memoryValid=false,networkValid=false;
    uint64_t memoryTotal=0,memoryUsed=0,processMemory=0,uptime=0;
    std::vector<Disk> disks;std::vector<Adapter> adapters;ULONG chosen=0;std::wstring networkName=L"正在读取网卡";
};
uint64_t number(FILETIME f){return (uint64_t(f.dwHighDateTime)<<32)|f.dwLowDateTime;}
std::wstring fixed(double n,int digits=0){std::wostringstream s;s<<std::fixed<<std::setprecision(digits)<<n;return s.str();}
std::wstring bytes(double n,bool rate=false){
    const wchar_t* units[]={L"B",L"KB",L"MB",L"GB",L"TB"};int i=0;
    while(n>=1024 && i<4){n/=1024;++i;}
    return fixed(n,i>0?1:0)+L" "+units[i]+(rate?L"/s":L"");
}
struct Collector {
    bool cpuReady=false,netReady=false;uint64_t idle=0,total=0;Clock::time_point last=Clock::now(),lastDisk{};
    std::map<ULONG,Adapter> previous;std::vector<Disk> disks;
    Snapshot sample(ULONG wanted){
        Snapshot s;auto now=Clock::now();double seconds=std::chrono::duration<double>(now-last).count();
        FILETIME i,k,u;
        if(GetSystemTimes(&i,&k,&u)){
            auto nextIdle=number(i),nextTotal=number(k)+number(u);
            if(cpuReady)s.cpu=cpu_percent(idle,total,nextIdle,nextTotal);
            idle=nextIdle;total=nextTotal;cpuReady=true;
        }
        MEMORYSTATUSEX mem{};mem.dwLength=sizeof(mem);
        if(GlobalMemoryStatusEx(&mem)){s.memoryValid=true;s.memoryTotal=mem.ullTotalPhys;s.memoryUsed=mem.ullTotalPhys-mem.ullAvailPhys;}
        PROCESS_MEMORY_COUNTERS pm{};
        if(GetProcessMemoryInfo(GetCurrentProcess(),&pm,sizeof(pm)))s.processMemory=pm.WorkingSetSize;
        s.uptime=GetTickCount64()/1000;
        if(lastDisk==Clock::time_point{} || now-lastDisk>=std::chrono::seconds(10)){
            disks.clear();wchar_t drives[512]{};DWORD count=GetLogicalDriveStringsW(511,drives);
            if(count && count<512)for(wchar_t* d=drives;*d;d+=wcslen(d)+1){
                if(GetDriveTypeW(d)!=DRIVE_FIXED)continue;
                ULARGE_INTEGER free{},all{},available{};
                if(GetDiskFreeSpaceExW(d,&available,&all,&free)&&all.QuadPart)disks.push_back({std::wstring(d,2),available.QuadPart,all.QuadPart});
            }
            lastDisk=now;
        }
        s.disks=disks;MIB_IF_TABLE2* table=nullptr;
        if(GetIfTable2(&table)==NO_ERROR){
            std::map<ULONG,Adapter> current;double highest=-1;Adapter selected;bool found=false;
            for(ULONG index=0;index<table->NumEntries;++index){
                const auto& row=table->Table[index];
                if(row.OperStatus!=IfOperStatusUp || (row.Type!=IF_TYPE_ETHERNET_CSMACD && row.Type!=IF_TYPE_IEEE80211))continue;
                if(row.InterfaceAndOperStatusFlags.FilterInterface || row.InterfaceAndOperStatusFlags.NotMediaConnected)continue;
                Adapter a{row.InterfaceIndex,row.Alias,row.InOctets,row.OutOctets,row.ReceiveLinkSpeed};
                current[a.id]=a;s.adapters.push_back(a);
                const auto before=previous.find(a.id);double down=0,up=0;
                bool valid=netReady && before!=previous.end() && seconds>0;
                if(valid){down=byte_rate(before->second.rx,a.rx,seconds);up=byte_rate(before->second.tx,a.tx,seconds);}
                if((wanted && wanted==a.id) || (!wanted && down+up>highest)){
                    highest=down+up;selected=a;s.down=down;s.up=up;s.networkValid=valid;found=true;
                }
            }
            if(found){s.chosen=selected.id;s.networkName=selected.name;}
            else s.networkName=wanted?L"所选网卡未连接（菜单可切回自动）":L"没有活动的以太网或 Wi-Fi";
            FreeMibTable(table);previous=std::move(current);netReady=true;
        }else s.networkName=L"网卡信息暂不可用";
        last=now;return s;
    }
};

HWND windowHandle=nullptr;float scale=1;bool expanded=false,light=false,pinned=true;std::atomic<int> interval{1000};
std::atomic<ULONG> wanted{0};std::atomic<bool> stopping{false};std::thread worker;
std::mutex dataMutex,waitMutex;std::condition_variable wake;Snapshot latest,current;
std::deque<double> cpuHistory,memoryHistory,downHistory,upHistory;ULONG historyAdapter=0;
std::wstring iniPath;int samples=0;
int px(float v){return int(std::lround(v*scale));}
int height(){return expanded?594:414;}
Color background(){return light?Color(242,246,250):Color(19,25,34);}
Color surface(){return light?Color(255,255,255):Color(29,38,50);}
Color ink(){return light?Color(30,47,64):Color(236,244,250);}
Color muted(){return light?Color(94,113,129):Color(149,169,187);}
Color green(){return light?Color(19,138,109):Color(94,218,177);}
Color blue(){return light?Color(49,117,204):Color(118,178,255);}
void text(Graphics& g,const std::wstring& value,float x,float y,float w,float h,float size,Color color,bool bold=false){
    Font font(L"Microsoft YaHei UI",size,bold?FontStyleBold:FontStyleRegular,UnitPixel);
    SolidBrush brush(color);StringFormat format;format.SetTrimming(StringTrimmingEllipsisCharacter);
    format.SetFormatFlags(StringFormatFlagsNoWrap);g.DrawString(value.c_str(),-1,&font,RectF(x,y,w,h),&format,&brush);
}
void rounded(Graphics& g,float x,float y,float w,float h,float r,Color color){
    GraphicsPath path;path.AddArc(x,y,r*2,r*2,180,90);path.AddArc(x+w-r*2,y,r*2,r*2,270,90);
    path.AddArc(x+w-r*2,y+h-r*2,r*2,r*2,0,90);path.AddArc(x,y+h-r*2,r*2,r*2,90,90);path.CloseFigure();
    SolidBrush brush(color);g.FillPath(&brush,&path);
}
void bar(Graphics& g,float x,float y,float w,double percent,Color color){
    rounded(g,x,y,w,5,2,light?Color(229,236,243):Color(47,61,76));
    if(percent>0)rounded(g,x,y,std::max(4.0f,w*float(std::clamp(percent,0.0,100.0))/100),5,2,color);
}
void graph(Graphics& g,const std::deque<double>& values,float x,float y,float w,float h,double max,Color color){
    if(values.size()<2)return;Pen pen(color,1.6f);std::vector<PointF> points;
    const float step=w/59;
    for(size_t i=0;i<values.size();++i)points.emplace_back(x+w-step*float(values.size()-1-i),y+h-float(std::clamp(values[i]/std::max(max,1.0),0.0,1.0))*h);
    g.DrawLines(&pen,points.data(),int(points.size()));
}
void diskRow(Graphics& g,const Disk& disk,float y){
    double used=100.0*(disk.total-disk.free)/disk.total;
    text(g,disk.name,28,y,32,22,13,ink(),true);
    text(g,bytes(double(disk.free))+L" 可用 / "+bytes(double(disk.total)),69,y,274,22,12,muted());
    bar(g,28,y+25,324,used,used>=90?Color(245,166,98):green());
}
void paint(HWND hwnd){
    PAINTSTRUCT ps;HDC dc=BeginPaint(hwnd,&ps);RECT client;GetClientRect(hwnd,&client);
    Bitmap buffer(client.right,client.bottom,PixelFormat32bppPARGB);Graphics g(&buffer);
    g.SetSmoothingMode(SmoothingModeAntiAlias);g.SetTextRenderingHint(TextRenderingHintClearTypeGridFit);g.Clear(background());g.ScaleTransform(scale,scale);
    rounded(g,16,18,28,28,9,green());text(g,L"状",21,20,24,25,17,background(),true);
    text(g,L"桌面状态",54,17,190,25,18,ink(),true);text(g,L"本机实时 · C++",54,43,210,19,11,muted());
    text(g,pinned?L"●":L"○",275,21,22,25,16,green());text(g,L"···",310,16,28,29,20,muted(),true);text(g,L"×",346,17,24,29,21,muted());
    rounded(g,16,78,169,119,14,surface());rounded(g,195,78,169,119,14,surface());
    text(g,L"CPU",28,91,132,21,12,muted(),true);
    text(g,current.cpu<0?L"采样中":fixed(current.cpu)+L"%",28,114,145,44,32,ink(),true);
    graph(g,cpuHistory,28,164,145,19,100,green());
    double mem=current.memoryTotal?100.0*current.memoryUsed/current.memoryTotal:0;
    text(g,L"内存",207,91,130,21,12,muted(),true);
    text(g,current.memoryValid?fixed(mem)+L"%":L"不可用",207,114,145,44,32,ink(),true);
    graph(g,memoryHistory,207,156,145,8,100,blue());
    text(g,current.memoryValid?bytes(double(current.memoryUsed))+L" / "+bytes(double(current.memoryTotal)):L"正在读取",207,168,149,20,10.5f,muted());
    rounded(g,16,207,348,110,14,surface());
    text(g,L"网络",28,218,55,21,12,muted(),true);text(g,current.networkName,79,218,269,21,11,muted());
    text(g,L"↓ "+(current.networkValid?bytes(current.down,true):L"采样中"),28,243,161,25,17,green(),true);
    text(g,L"↑ "+(current.networkValid?bytes(current.up,true):L"采样中"),207,243,145,25,17,blue(),true);
    double maxRate=1024;
    for(double v:downHistory)maxRate=std::max(maxRate,v);for(double v:upHistory)maxRate=std::max(maxRate,v);
    graph(g,downHistory,28,278,324,25,maxRate,green());graph(g,upHistory,28,278,324,25,maxRate,blue());
    rounded(g,16,327,348,55,12,surface());
    if(!current.disks.empty())diskRow(g,current.disks.front(),334);else text(g,L"磁盘信息暂不可用",28,341,320,25,12,muted());
    if(expanded){
        rounded(g,16,392,348,164,14,surface());text(g,L"设备详情",28,403,310,22,13,ink(),true);
        float y=430;
        for(size_t i=1;i<current.disks.size() && i<3;++i){diskRow(g,current.disks[i],y);y+=43;}
        if(current.disks.size()==1)text(g,L"当前仅检测到一个可读取的固定磁盘",28,y,320,20,11,muted());
        text(g,L"已运行 "+fixed(double(current.uptime/3600))+L" 小时 "+fixed(double(current.uptime%3600/60))+L" 分钟",28,523,199,21,11,muted());
        text(g,L"本卡片 "+bytes(double(current.processMemory)),218,523,135,21,11,muted());
    }
    text(g,L"Ctrl + Alt + F9 打开",20,float(height()-25),218,20,10.5f,muted());
    text(g,expanded?L"收起详情  ↑":L"展开详情  ↓",266,float(height()-26),104,22,11,green(),true);
    Graphics out(dc);out.DrawImage(&buffer,0,0);EndPaint(hwnd,&ps);
}
void append(std::deque<double>& values,double v){values.push_back(v);if(values.size()>60)values.pop_front();}
void shape(HWND hwnd){
    HRGN region=CreateRoundRectRgn(0,0,px(380)+1,px(float(height()))+1,px(28),px(28));
    if(!SetWindowRgn(hwnd,region,TRUE))DeleteObject(region);
}
void resizeCard(HWND hwnd){
    RECT r;GetWindowRect(hwnd,&r);MONITORINFO m{sizeof(m)};GetMonitorInfoW(MonitorFromWindow(hwnd,MONITOR_DEFAULTTONEAREST),&m);
    int x=std::clamp<int>(r.left,m.rcWork.left,std::max<int>(m.rcWork.left,m.rcWork.right-px(380)));
    int y=std::clamp<int>(r.top,m.rcWork.top,std::max<int>(m.rcWork.top,m.rcWork.bottom-px(float(height()))));
    SetWindowPos(hwnd,pinned?HWND_TOPMOST:HWND_NOTOPMOST,x,y,px(380),px(float(height())),SWP_NOACTIVATE);shape(hwnd);InvalidateRect(hwnd,nullptr,FALSE);
}
void saveSettings(HWND hwnd){
    RECT r;GetWindowRect(hwnd,&r);
    for(auto pair:std::vector<std::pair<std::wstring,int>>{{L"x",r.left},{L"y",r.top},{L"light",light},{L"expanded",expanded},{L"pinned",pinned},{L"interval",interval.load()}})
        WritePrivateProfileStringW(L"card",pair.first.c_str(),std::to_wstring(pair.second).c_str(),iniPath.c_str());
}
void showMenu(HWND hwnd){
    HMENU menu=CreatePopupMenu(),speed=CreatePopupMenu(),network=CreatePopupMenu();
    AppendMenuW(menu,MF_STRING|(pinned?MF_CHECKED:0),1,L"始终置顶");
    AppendMenuW(menu,MF_STRING|(light?MF_CHECKED:0),2,L"浅色外观");
    AppendMenuW(menu,MF_STRING|(expanded?MF_CHECKED:0),3,L"展开详情");
    for(auto pair:std::vector<std::pair<int,const wchar_t*>>{{1000,L"每秒"},{2000,L"每2秒"},{5000,L"每5秒"}})
        AppendMenuW(speed,MF_STRING|(interval==pair.first?MF_CHECKED:0),100+pair.first,pair.second);
    AppendMenuW(menu,MF_POPUP,reinterpret_cast<UINT_PTR>(speed),L"刷新频率");
    AppendMenuW(network,MF_STRING|(wanted==0?MF_CHECKED:0),200,L"自动选择最活跃网卡");
    for(size_t i=0;i<current.adapters.size();++i){
        auto a=current.adapters[i];auto name=a.name;size_t start=0;while((start=name.find(L'&',start))!=std::wstring::npos){name.insert(start,L"&");start+=2;}
        AppendMenuW(network,MF_STRING|(wanted==a.id?MF_CHECKED:0),300+i,name.c_str());
    }
    AppendMenuW(menu,MF_POPUP,reinterpret_cast<UINT_PTR>(network),L"网速来源");
    AppendMenuW(menu,MF_SEPARATOR,0,nullptr);AppendMenuW(menu,MF_STRING,4,L"说明与全部磁盘…");
    AppendMenuW(menu,MF_STRING,5,L"退出（快捷键可再次打开）");
    POINT point;GetCursorPos(&point);SetForegroundWindow(hwnd);
    int command=TrackPopupMenu(menu,TPM_RETURNCMD|TPM_RIGHTBUTTON,point.x,point.y,0,hwnd,nullptr);DestroyMenu(menu);
    if(command==1){pinned=!pinned;resizeCard(hwnd);}
    else if(command==2){light=!light;InvalidateRect(hwnd,nullptr,FALSE);}
    else if(command==3){expanded=!expanded;resizeCard(hwnd);}
    else if(command==5)SendMessageW(hwnd,WM_CLOSE,0,0);
    else if(command==4){
        std::wstring msg=L"拖动顶部移动卡片；点右上角 × 退出卡片并停止采样。\nCtrl + Alt + F9 由独立快捷键启动器响应；托盘菜单可退出启动器。\n下次登录后双击桌面入口即可重新启用，不添加开机启动。\n\nCPU、内存与网速按所选频率采样，磁盘空间每10秒读取。\n图表保留最近60次采样；网速单位为字节/秒。\n自动网卡只选流量最大的一张，不累加虚拟网卡。\n不读取文件内容，不联网发送数据。\n\n";
        for(auto& d:current.disks)msg+=d.name+L"  可用 "+bytes(double(d.free))+L" / "+bytes(double(d.total))+L"\n";
        MessageBoxW(hwnd,msg.c_str(),L"桌面状态卡片 · 使用说明",MB_OK|MB_ICONINFORMATION);
    }else if(command>=1100 && command<=5100){interval=command-100;wake.notify_all();}
    else if(command==200 || (command>=300 && command<int(300+current.adapters.size()))){
        wanted=command==200?0:current.adapters[command-300].id;downHistory.clear();upHistory.clear();historyAdapter=0;
    }
}
LRESULT CALLBACK procedure(HWND hwnd,UINT message,WPARAM w,LPARAM l){
    switch(message){
    case WM_CREATE:
        windowHandle=hwnd;scale=GetDpiForWindow(hwnd)/96.0f;resizeCard(hwnd);
        worker=std::thread([hwnd]{Collector collector;while(!stopping){
            Snapshot next=collector.sample(wanted.load());{std::lock_guard<std::mutex> lock(dataMutex);latest=std::move(next);}
            PostMessageW(hwnd,SAMPLE,0,0);std::unique_lock<std::mutex> lock(waitMutex);wake.wait_for(lock,std::chrono::milliseconds(interval.load()),[]{return stopping.load();});
        }});return 0;
    case SAMPLE:
        {std::lock_guard<std::mutex> lock(dataMutex);current=latest;}
        if(current.cpu>=0)append(cpuHistory,current.cpu);
        if(current.memoryValid && current.memoryTotal)append(memoryHistory,100.0*current.memoryUsed/current.memoryTotal);
        if(historyAdapter!=current.chosen){downHistory.clear();upHistory.clear();historyAdapter=current.chosen;}
        if(current.networkValid){append(downHistory,current.down);append(upHistory,current.up);}
        ++samples;InvalidateRect(hwnd,nullptr,FALSE);return 0;
    case WM_ERASEBKGND:return 1;
    case WM_PAINT:paint(hwnd);return 0;
    case WM_NCHITTEST:{POINT p{GET_X_LPARAM(l),GET_Y_LPARAM(l)};ScreenToClient(hwnd,&p);
        if(p.y<px(70) && p.x<px(265))return HTCAPTION;return HTCLIENT;}
    case WM_LBUTTONUP:{float x=GET_X_LPARAM(l)/scale,y=GET_Y_LPARAM(l)/scale;
        if(y<64 && x>=342)SendMessageW(hwnd,WM_CLOSE,0,0);
        else if(y<64 && x>=305)showMenu(hwnd);
        else if(y<64 && x>=268){pinned=!pinned;resizeCard(hwnd);}
        else if(y>height()-35 && x>250){expanded=!expanded;resizeCard(hwnd);}
        return 0;}
    case WM_RBUTTONUP:showMenu(hwnd);return 0;
    case WM_KEYDOWN:if(w==VK_ESCAPE){SendMessageW(hwnd,WM_CLOSE,0,0);return 0;}break;
    case WM_DPICHANGED:{scale=HIWORD(w)/96.0f;auto r=reinterpret_cast<RECT*>(l);
        SetWindowPos(hwnd,nullptr,r->left,r->top,px(380),px(float(height())),SWP_NOZORDER|SWP_NOACTIVATE);shape(hwnd);return 0;}
    case WM_DISPLAYCHANGE:resizeCard(hwnd);return 0;
    case WM_CLOSE:saveSettings(hwnd);DestroyWindow(hwnd);return 0;
    case WM_DESTROY:stopping=true;wake.notify_all();if(worker.joinable())worker.join();PostQuitMessage(0);return 0;
    }
    return DefWindowProcW(hwnd,message,w,l);
}
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,LPWSTR,int){
    int argc=0;LPWSTR* argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    if(argc==3 && std::wstring(argv[1])==L"--probe"){
        Collector collector;collector.sample(0);Sleep(250);auto s=collector.sample(0);
        std::ofstream out{std::filesystem::path(argv[2])};
        out<<"{\"cpu\":"<<s.cpu<<",\"memory_total\":"<<s.memoryTotal<<",\"memory_used\":"<<s.memoryUsed
            <<",\"disk_count\":"<<s.disks.size()<<",\"adapter_count\":"<<s.adapters.size()<<",\"down\":"<<s.down<<",\"up\":"<<s.up<<"}";
        bool ok=out.good() && s.cpu>=0 && s.cpu<=100 && s.memoryValid && s.memoryUsed<=s.memoryTotal;
        LocalFree(argv);return ok?0:2;
    }
    LocalFree(argv);
    HANDLE mutex=CreateMutexW(nullptr,TRUE,L"Local\\CodexDesktopStatusCardV1");
    if(!mutex)return 3;
    if(GetLastError()==ERROR_ALREADY_EXISTS){
        for(int i=0;i<20;++i){HWND old=FindWindowW(CLASSNAME,TITLE);if(old){ShowWindow(old,SW_RESTORE);SetForegroundWindow(old);break;}Sleep(100);}
        CloseHandle(mutex);return 0;
    }
    wchar_t path[32768];GetModuleFileNameW(nullptr,path,32768);iniPath=(std::filesystem::path(path).parent_path()/L"settings.ini").wstring();
    light=GetPrivateProfileIntW(L"card",L"light",0,iniPath.c_str())!=0;expanded=GetPrivateProfileIntW(L"card",L"expanded",0,iniPath.c_str())!=0;
    pinned=GetPrivateProfileIntW(L"card",L"pinned",1,iniPath.c_str())!=0;int savedInterval=GetPrivateProfileIntW(L"card",L"interval",1000,iniPath.c_str());
    interval=(savedInterval==2000 || savedInterval==5000)?savedInterval:1000;
    GdiplusStartupInput input;ULONG_PTR token;if(GdiplusStartup(&token,&input,nullptr)!=Ok){CloseHandle(mutex);return 4;}
    WNDCLASSEXW wc{sizeof(wc)};wc.lpfnWndProc=procedure;wc.hInstance=instance;wc.lpszClassName=CLASSNAME;
    wc.hCursor=LoadCursorW(nullptr,IDC_ARROW);wc.hIcon=LoadIconW(nullptr,IDI_APPLICATION);wc.hIconSm=wc.hIcon;RegisterClassExW(&wc);
    scale=GetDpiForSystem()/96.0f;RECT area;SystemParametersInfoW(SPI_GETWORKAREA,0,&area,0);
    int x=GetPrivateProfileIntW(L"card",L"x",area.right-px(402),iniPath.c_str());int y=GetPrivateProfileIntW(L"card",L"y",area.top+px(28),iniPath.c_str());
    HWND hwnd=CreateWindowExW(WS_EX_APPWINDOW,CLASSNAME,TITLE,WS_POPUP|WS_MINIMIZEBOX,x,y,px(380),px(float(height())),nullptr,nullptr,instance,nullptr);
    if(!hwnd){GdiplusShutdown(token);CloseHandle(mutex);return 5;}
    ShowWindow(hwnd,SW_SHOWNORMAL);UpdateWindow(hwnd);MSG msg{};
    while(GetMessageW(&msg,nullptr,0,0)>0){TranslateMessage(&msg);DispatchMessageW(&msg);}
    GdiplusShutdown(token);ReleaseMutex(mutex);CloseHandle(mutex);return 0;
}
