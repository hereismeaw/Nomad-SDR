/* SPDX-License-Identifier: MIT */
#include "compact.h"

static int32_t component(const uint8_t *p) {
    uint32_t v=p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16;
    return (int32_t)(v&0x3fffffu)-(int32_t)(v&0x400000u);
}
static bool pack_components(uint8_t *dst,const uint8_t *src,unsigned count) {
    uint32_t peak=0;
    for (unsigned i=0;i<count;++i) {
        if (src[3*i+2]&0x80) return false;
        int32_t v=component(src+3*i);
        uint32_t magnitude=(uint32_t)(v<0?-v:v);
        if (magnitude>peak) peak=magnitude;
    }
    unsigned shift=0;
    while (peak>(127u<<shift)) ++shift;
    dst[0]=(uint8_t)shift;
    for (unsigned i=0;i<count;++i) {
        int32_t v=component(src+3*i);
        uint32_t magnitude=(uint32_t)(v<0?-v:v);
        if (shift) magnitude=(magnitude+(1u<<(shift-1)))>>shift;
        int32_t value=v<0?-(int32_t)magnitude:(int32_t)magnitude;
        dst[i+1]=(uint8_t)value;
    }
    return true;
}
bool nomad_pack8(uint8_t *dst,const uint8_t *src) {
    return pack_components(dst,src,250);
}
bool nomad_arc8(uint8_t *dst,const uint8_t *src,uint32_t sequence) {
    uint32_t marker=(uint32_t)src[0]<<24|(uint32_t)src[1]<<16|(uint32_t)src[2]<<8|src[3];
    unsigned shift=(marker>>24)&127;
    if(!(marker&0x80000000u) || shift>16 || (marker&0xffffffu)!=((sequence+1)&0xffffffu))return false;
    dst[0]=(uint8_t)shift;
    for(unsigned i=0;i<250;++i) {
        unsigned offset=i+4;
        dst[i+1]=src[(offset&~3u)+3-(offset&3)];
    }
    return true;
}
bool nomad_expand8(uint8_t *dst,const uint8_t *src) {
    if(src[0]>16)return false;
    for(unsigned i=0;i<250;++i) {
        int32_t value=(int32_t)(int8_t)src[i+1]*(int32_t)(1u<<src[0]);
        if(value>4194303)value=4194303;
        if(value< -4194304)value= -4194304;
        uint32_t bits=(uint32_t)value&0x7fffffu;
        dst[3*i]=(uint8_t)bits;dst[3*i+1]=(uint8_t)(bits>>8);dst[3*i+2]=(uint8_t)(bits>>16);
    }
    return true;
}

/* firwin(33, .4), Hamming window, Q15, exact unity DC gain. */
static const int16_t taps[33]={50,0,-81,-74,110,256,0,-496,-413,551,1183,0,
    -2144,-1884,2956,9824,13092,9824,2956,-1884,-2144,0,1183,551,-413,-496,
    0,256,110,-74,-81,0,50};
static void encode(uint8_t *p,int64_t sum) {
    int64_t value=sum<0?-((-sum+16384)/32768):(sum+16384)/32768;
    if(value>4194303)value=4194303;
    if(value< -4194304)value= -4194304;
    uint32_t v=(uint32_t)value&0x7fffff;
    p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);p[2]=(uint8_t)(v>>16);
}
unsigned nomad_decimate8(uint8_t *dst,const uint8_t *src,nomad_decimator_t *state) {
    uint8_t filtered[63*6];
    unsigned count=0;
    for(unsigned n=0;n<125;++n) {
        const uint8_t *sample=src+n*6;
        if((sample[2]|sample[5])&0x80)return 0;
        state->i[state->position]=component(sample);
        state->q[state->position]=component(sample+3);
        if(!state->phase) {
            int64_t i=0,q=0;
            unsigned cursor=state->position;
            for(unsigned tap=0;tap<33;++tap) {
                i+=(int64_t)state->i[cursor]*taps[tap];
                q+=(int64_t)state->q[cursor]*taps[tap];
                cursor=cursor?cursor-1:32;
            }
            encode(filtered+count*6,i);encode(filtered+count*6+3,q);++count;
        }
        state->phase^=1;
        state->position=(state->position+1)%33;
    }
    return pack_components(dst,filtered,count*2)?count:0;
}
