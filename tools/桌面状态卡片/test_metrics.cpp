#include "metrics.hpp"
#include <cassert>
#include <iostream>
int main(){
    assert(cpu_percent(100,1000,150,1200)==75);
    assert(cpu_percent(100,1000,100,1000)==-1);
    assert(cpu_percent(100,1000,400,1200)==-1);
    assert(cpu_percent(100,1000,90,1200)==-1);
    assert(byte_rate(100,1124,2)==512);
    assert(byte_rate(1124,100,2)==0);
    assert(byte_rate(100,1124,0)==0);
    std::cout<<"PASS: CPU deltas, first sample, counter reset and real elapsed network rates\n";
}
