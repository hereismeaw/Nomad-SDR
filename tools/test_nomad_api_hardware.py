#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Receive-only hardware checks through the real local HTTP API.

No RF transmission. Packet reception and CAD detection need a reference signal
for positive-path RF validation; this script checks configuration/lifecycle.
"""
import argparse
import json
from pathlib import Path
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'host'))
from nomad_api import create_server
from nomad_control import Board,Control


def main():
    p=argparse.ArgumentParser(description=__doc__)
    endpoints=p.add_mutually_exclusive_group(required=True)
    endpoints.add_argument('--serial');endpoints.add_argument('--host')
    p.add_argument('--report',type=Path,default=Path('build/api-hardware.json'))
    args=p.parse_args()
    control=Control(Board(args.serial,args.host));server=create_server(control,port=0)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    base=f'http://127.0.0.1:{server.server_port}/api/v1'
    report=dict(complete=False,checks=[],rf_reference_used=False)
    def call(path,data=None,expected=200):
        request=Request(base+path,data=None if data is None else json.dumps(data).encode(),
                        headers={'Content-Type':'application/json'},method='GET' if data is None else 'POST')
        try:
            with urlopen(request,timeout=20) as response:
                status=response.status;body=response.read()
        except HTTPError as exc:status=exc.code;body=exc.read()
        value=json.loads(body) if not path.endswith('.csv') else body.decode()
        report['checks'].append(dict(path=path,status=status,response=value))
        if status!=expected:raise RuntimeError(f'{path}: expected {expected}, got {status}: {value}')
        return value['result'] if isinstance(value,dict) and 'result' in value else value
    def wait_job(radio,kind):
        until=time.monotonic()+15
        while time.monotonic()<until:
            result=call(f'/radios/{radio}/{kind}/status')
            if result['state'] not in ('running',):
                if result['state']=='error':raise RuntimeError(result['error'])
                return result
            time.sleep(.1)
        raise RuntimeError('Job did not finish in time')
    try:
        caps=call('/capabilities');assert caps['native']['radios']==2
        call('/radios/0/stream/status')
        call('/radios/0/rx/configure',dict(frequency_hz=915000000,modem='lora',sf=7))
        call('/radios/0/diagnostics')
        call('/radios/0/gain',dict(agc=False,step=4,rx_boosted=True,lna='differential'))
        call('/radios/0/rx/start',{})
        for topology in ('single_n','single_p','differential'):
            call('/radios/0/gain',dict(lna=topology))
        call('/radios/0/diagnostics')
        assert call('/radios/0/status')['running']
        cad=call('/radios/0/cad',dict(timeout_ms=1000));assert not cad['timeout']
        call('/radios/0/gain',dict(agc=True,rx_boosted=False))
        call('/radios/0/rx/stop',{})
        call('/radios/0/sweep/start',dict(start_hz=915000000,stop_hz=915200000,step_hz=100000,dwell_ms=2,samples=2))
        job=wait_job(0,'sweep');assert job['count']==3
        call('/jobs/'+job['id']);call('/jobs/'+job['id']+'.csv')
        call('/radios/0/packet/configure',dict(modem='gfsk',frequency_hz=915000000))
        call('/radios/0/packet/start',dict(duration_s=.3));wait_job(0,'packet')
        call('/dual/configure',dict(radios=[
            dict(mode='sweep',settings=dict(start_hz=915000000,stop_hz=915200000,step_hz=100000,dwell_ms=2,samples=1,cycles=0)),
            dict(mode='packet',settings=dict(profile=dict(modem='lora',frequency_hz=2440000000))) ]))
        call('/dual/start',{});time.sleep(.4)
        state=call('/dual/status')
        assert all(r['job']['state']=='running' for r in state['radios'])
        assert state['radios'][0]['job']['count']>0
        call('/radios/0/rx/configure',{},expected=409)
        call('/radios/0/packet/stop',{},expected=409)
        call('/dual/stop',{})
        assert all(r['job']['state'] in ('cancelled','complete') for r in call('/dual/status')['radios'])
        call('/radios/1/diagnostics')
        call('/radios/0/gain');call('/radios/0/status')
        call('/radios/0/cad',dict(symbols=3),expected=400)
        call('/radios/0/rx/configure',dict(frequency_hz=1),expected=400)
        call('/unknown',expected=404)
        report['complete']=True
    except BaseException as exc:
        report['error']=str(exc);raise
    finally:
        server.shutdown();worker.join(3);server.server_close();control.close()
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(complete=True,http_checks=len(report['checks']),report=str(args.report))))


if __name__=='__main__':main()
