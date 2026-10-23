#pragma once
#include <algorithm>
#include <cstdint>

inline double cpu_percent(uint64_t idle0,uint64_t total0,uint64_t idle1,uint64_t total1) {
    if(total1<=total0 || idle1<idle0)return -1;
    const auto total=total1-total0,idle=idle1-idle0;
    if(idle>total)return -1;
    return std::clamp(100.0*(total-idle)/total,0.0,100.0);
}
inline double byte_rate(uint64_t before,uint64_t after,double seconds) {
    return seconds>0 && after>=before ? double(after-before)/seconds : 0;
}
