/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "compact.h"
static void encode(uint8_t *p,int32_t value) {
    uint32_t v=(uint32_t)value&0x7fffff;
    p[0]=v; p[1]=v>>8; p[2]=v>>16;
}
static double tone(double frequency) {
    nomad_decimator_t state={0};uint8_t input[750],output[251];
    double power=0;unsigned count=0;
    for(unsigned block=0;block<40;++block) {
        for(unsigned n=0;n<125;++n) {
            double phase=2*3.141592653589793*frequency*(block*125+n)/62500;
            encode(input+n*6,(int32_t)(1000000*cos(phase)));
            encode(input+n*6+3,(int32_t)(1000000*sin(phase)));
        }
        unsigned samples=nomad_decimate8(output,input,&state);
        assert(samples==(block%2?62u:63u));
        if(block>1)for(unsigned i=0;i<samples;++i) {
            double iv=(int8_t)output[1+2*i]*(1<<output[0]);
            double qv=(int8_t)output[2+2*i]*(1<<output[0]);
            power+=iv*iv+qv*qv;++count;
        }
    }
    return sqrt(power/count)/1000000;
}
int main(void) {
    uint8_t input[750],output[251];
    uint8_t arc[256]={0};
    arc[0]=0x85;arc[3]=1;
    for(unsigned i=0;i<250;++i) {
        unsigned offset=i+4;
        arc[(offset&~3u)+3-(offset&3)]=(uint8_t)i;
    }
    assert(nomad_arc8(output,arc,0));assert(output[0]==5);
    for(unsigned i=0;i<250;++i)assert(output[i+1]==(uint8_t)i);
    assert(!nomad_arc8(output,arc,1));
    arc[0]=0x91;assert(!nomad_arc8(output,arc,0));
    arc[0]=5;assert(!nomad_arc8(output,arc,0));
    arc[0]=0x85;arc[3]=0;
    assert(nomad_arc8(output,arc,0xffffff));
    assert(nomad_expand8(input,output));
    for(unsigned i=0;i<250;++i) {
        int32_t value=(int32_t)(input[3*i]|(uint32_t)input[3*i+1]<<8|(uint32_t)input[3*i+2]<<16);
        value=(value&0x3fffff)-(value&0x400000);
        assert(value==(int8_t)i*32);
    }
    output[0]=16;output[1]=127;output[2]=128;
    assert(nomad_expand8(input,output));
    assert(input[0]==255 && input[1]==255 && input[2]==63);
    assert(input[3]==0 && input[4]==0 && input[5]==64);
    output[0]=17;assert(!nomad_expand8(input,output));
    uint32_t random=12345;
    for (unsigned trial=0;trial<200;++trial) {
        int32_t originals[250];
        for (unsigned i=0;i<250;++i) {
            random=random*1664525u+1013904223u;
            int32_t v=(int32_t)(random&0x7fffff)-4194304;
            if (trial<16) v/=(1<<trial);
            originals[i]=v; encode(input+3*i,v);
        }
        assert(nomad_pack8(output,input)); assert(output[0]<=16);
        int32_t scale=1<<output[0];
        for (unsigned i=0;i<250;++i) assert(abs((int8_t)output[i+1]*scale-originals[i])<=scale/2);
    }
    memset(input,0,sizeof(input)); assert(nomad_pack8(output,input));
    for (unsigned i=0;i<251;++i) assert(output[i]==0);
    encode(input,-4194304); encode(input+3,4194303);
    assert(nomad_pack8(output,input)); assert((int8_t)output[1]<0 && (int8_t)output[2]>0);
    input[2]|=0x80; assert(!nomad_pack8(output,input));
    double pass=tone(5000),stop=tone(22000);
    assert(pass>.98 && pass<1.02);assert(stop<.02);
    printf("FIR /2: passband gain %.4f, alias rejection %.1f dB\n",pass,20*log10(stop));
    puts("Compact I/Q: signed extremes, random quantization bounds and invalid containers passed");
}
