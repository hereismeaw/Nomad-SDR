#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Local JSON control API for Nomad RX, sweep, packet, CAD, gain and dual jobs."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
import re
from urllib.parse import urlsplit

from bridge import BridgeError
from nomad_control import Board, BusyError, Control, export_job


def create_server(control, listen='127.0.0.1', port=8094, output=Path('build/nomad-api')):
    class Handler(BaseHTTPRequestHandler):
        server_version='NomadAPI/1'

        def log_message(self,fmt,*args):
            logging.info(fmt,*args)

        def reply(self,code,value,content_type='application/json'):
            payload=(json.dumps(value,allow_nan=False)+'\n').encode() if content_type=='application/json' else value
            self.send_response(code);self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(payload)));self.send_header('Cache-Control','no-store')
            self.end_headers();self.wfile.write(payload)

        def dispatch(self,method,path,data):
            if path=='/api/v1/capabilities' and method=='GET':return control.capabilities()
            if path=='/api/v1/dual/status' and method=='GET':
                return dict(plan=control.dual_plan,radios=[r.status() for r in control.radios])
            if path=='/api/v1/dual/configure' and method=='POST':return control.dual_configure(data)
            if path=='/api/v1/dual/start' and method=='POST':
                if data:raise ValueError('dual/start takes an empty object')
                return control.dual_start()
            if path=='/api/v1/dual/stop' and method=='POST':
                if data:raise ValueError('dual/stop takes an empty object')
                return dict(radios=[r.stop() if r.profile else r.status() for r in control.radios])
            match=re.fullmatch(r'/api/v1/jobs/([0-9a-f]{32})(\.csv)?',path)
            if match and method=='GET':
                for radio in control.radios:
                    job=radio.jobs.get(match[1])
                    if job:
                        if match[2]:
                            path=export_job(job,Path(output)/(job.id+'.csv'))
                            return path.read_bytes(),'text/csv; charset=utf-8'
                        return job.snapshot()
                raise KeyError('Unknown job')
            match=re.fullmatch(r'/api/v1/radios/([01])/(.+)',path)
            if not match:raise KeyError('Unknown endpoint')
            radio=control.radios[int(match[1])];action=match[2]
            if method=='GET':
                if action=='status':return radio.status()
                if action=='diagnostics':return radio.diagnostics()
                if action=='gain':return dict(radio.gain)
                if action=='stream/status':
                    status=control.board.view(radio.index).request('stream status')
                    return dict(stream=status['radios'][radio.index],uptime_ms=status['uptime_ms'],free_heap=status['free_heap'])
                if action in ('sweep/status','packet/status'):
                    job=radio.job
                    return job.snapshot() if job and job.kind==action.split('/')[0] else dict(state='idle')
            if method=='POST':
                if action in ('rx/configure','packet/configure'):return radio.configure(data)
                if action in ('rx/start','rx/stop','sweep/stop','packet/stop'):
                    if data:raise ValueError('This action takes an empty object')
                    if action=='rx/start':return radio.start()
                    if action=='rx/stop':return radio.stop()
                    return radio.stop_job(action.split('/')[0])
                if action=='gain':return radio.set_gain(data)
                if action=='cad':return radio.cad(data)
                if action=='sweep/start':return radio.sweep(data)
                if action=='packet/start':return radio.packet_start(data)
            raise KeyError('Unknown endpoint or HTTP method')

        def handle_request(self,method):
            try:
                path=urlsplit(self.path).path
                data={}
                if method=='POST':
                    if self.headers.get('Transfer-Encoding'):raise ValueError('Chunked requests are unsupported')
                    size=int(self.headers.get('Content-Length','0'))
                    if not 0<=size<=16384:raise ValueError('JSON body limit is 16384 bytes')
                    self.connection.settimeout(5)
                    data=json.loads(self.rfile.read(size)) if size else {}
                    if not isinstance(data,dict):raise ValueError('JSON object required')
                result=self.dispatch(method,path,data)
                if isinstance(result,tuple):self.reply(200,result[0],result[1])
                else:self.reply(200,dict(ok=True,result=result))
            except BusyError as exc:self.reply(409,dict(ok=False,error=str(exc)))
            except (ValueError,TypeError,json.JSONDecodeError) as exc:self.reply(400,dict(ok=False,error=str(exc)))
            except KeyError as exc:self.reply(404,dict(ok=False,error=str(exc)))
            except (BridgeError,RuntimeError,OSError) as exc:self.reply(502,dict(ok=False,error=str(exc)))

        def do_GET(self):self.handle_request('GET')
        def do_POST(self):self.handle_request('POST')

    server=ThreadingHTTPServer((listen,port),Handler)
    server.daemon_threads=True
    return server


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    endpoints=parser.add_mutually_exclusive_group(required=True)
    endpoints.add_argument('--serial');endpoints.add_argument('--host')
    parser.add_argument('--listen',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8094)
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
    control=Control(Board(serial=args.serial,host=args.host))
    server=create_server(control,args.listen,args.port)
    logging.info('Nomad API: http://%s:%s/api/v1/capabilities',args.listen,server.server_address[1])
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();control.close()


if __name__=='__main__':main()
