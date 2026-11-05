# SPDX-License-Identifier: GPL-3.0-only
import io
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import Mock,patch
from urllib.error import HTTPError
from urllib.request import Request,urlopen

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nomad_api import create_server
from nomad_control import Board,BusyError,Control,Job,Radio,packet_options,packet_record,sweep_options,validate_profile


class ControlTests(unittest.TestCase):
    def test_receive_control_api_never_issues_tx_opcode(self):
        factory=Mock();radio=Radio(Board(serial='COM3',factory=factory),0)
        for opcode in ('020affffff','0219','021a','020c00000000000000'):
            with self.assertRaisesRegex(ValueError,'RX control API'):radio.write(opcode)
        factory.assert_not_called()

    def test_profile_families_and_defaults(self):
        self.assertEqual(validate_profile({})['bandwidth_hz'],125000)
        self.assertEqual(validate_profile(dict(frequency_hz=2440000000))['bandwidth_hz'],203125)
        self.assertEqual(validate_profile(dict(modem='gfsk'))['sync_word'],'12345678')

    def test_bad_profiles_rejected_without_board_io(self):
        factory=Mock();radio=Radio(Board(serial='COM3',factory=factory),0)
        for options in (dict(frequency_hz=True),dict(frequency_hz=100000000),dict(sf=13),
                        dict(transmit=True),dict(crc=1),dict(frequency_hz=2440000000,bandwidth_hz=125000),
                        dict(modem='gfsk',sync_word='      '),dict(modem='gfsk',bit_rate=100000,bandwidth_hz=4800),
                        dict(modem='gfsk',sf=7),dict(modem='lora',bit_rate=10000)):
            with self.subTest(options=options),self.assertRaises(ValueError):radio.configure(options)
        factory.assert_not_called()

    def test_sweep_and_packet_bounds(self):
        for options in (dict(step_hz=0),dict(start_hz=915000000,stop_hz=914000000),
                        dict(start_hz=150000000,stop_hz=2500000000,step_hz=1),
                        dict(start_hz=2200000000,stop_hz=2400000000),dict(profile=None)):
            with self.subTest(options=options),self.assertRaises(ValueError):sweep_options(options)
        for options in (dict(duration_s=float('nan')),dict(duration_s=-1),dict(poll_ms=0),dict(capacity=4097)):
            with self.subTest(options=options),self.assertRaises(ValueError):packet_options(options)

    def test_packet_metrics_signed_snr_crc_and_missing_crc(self):
        row=packet_record('lora',b'abc',bytes([140,248,138]),8)
        self.assertEqual((row['rssi_dbm'],row['snr_db'],row['signal_rssi_dbm']),(-70,-2,-69))
        self.assertEqual(row['payload_hex'],'616263');self.assertTrue(row['crc_ok'])
        self.assertFalse(packet_record('lora',b'',bytes(3),128)['crc_ok'])
        self.assertFalse(packet_record('gfsk',b'',bytes([120,122,0,16]),8)['crc_ok'])
        self.assertIsNone(packet_record('lora',b'',bytes(3),8,False)['crc_ok'])

    def test_job_retention_has_explicit_evictions(self):
        job=Job('packet',capacity=2)
        for i in range(5):job.add(dict(value=i))
        state=job.snapshot()
        self.assertEqual(state['count'],5);self.assertEqual(state['buffer_evictions'],3)
        self.assertEqual([r['value'] for r in state['results']],[3,4])
        self.assertIsNone(state['counters']['hardware_drops'])

    def test_background_cancel_and_busy_operations(self):
        radio=Radio(Board(serial='COM3',factory=Mock()),0)
        radio._stop=Mock()
        radio.launch('sweep',lambda job:job.cancel.wait(2))
        with self.assertRaises(BusyError):radio.configure({})
        with self.assertRaises(BusyError):radio.stop_job('packet')
        status=radio.stop_job('sweep')
        self.assertEqual(status['state'],'cancelled');radio._stop.assert_called_once()

    def test_background_failure_remains_visible_and_cleans_up(self):
        radio=Radio(Board(serial='COM3',factory=Mock()),0);radio._stop=Mock()
        def fail(job):raise RuntimeError('SPI failure')
        radio.launch('packet',fail);radio.job.thread.join(2)
        status=radio.job.snapshot()
        self.assertEqual(status['state'],'error');self.assertEqual(status['error'],'SPI failure')
        radio._stop.assert_called_once()

    def test_dual_validates_both_plans_before_hardware(self):
        factory=Mock();control=Control(Board(serial='COM3',factory=factory))
        with self.assertRaises(ValueError):control.dual_configure(dict(radios=[dict(mode='packet'),dict(mode='sweep',settings=dict(step_hz=0))]))
        self.assertIsNone(control.dual_plan);factory.assert_not_called()

    def test_dual_start_failure_stops_first_job(self):
        control=Control(Board(serial='COM3',factory=Mock()))
        control.dual_configure(dict(radios=[dict(mode='packet'),dict(mode='packet')]))
        control.radios[0].packet_start=Mock(return_value={})
        control.radios[1].packet_start=Mock(side_effect=RuntimeError('configure failed'))
        for r in control.radios:r.stop_job=Mock()
        with self.assertRaisesRegex(RuntimeError,'configure failed'):control.dual_start()
        for r in control.radios:r.stop_job.assert_called_once()

    def test_uart_selection_and_command_are_atomic_between_jobs(self):
        recorded=[]
        class FakeBridge:
            _desynced=False
            def __init__(self,*args,nomad_radio=None,**kwargs):self.selected=nomad_radio
            def request(self,command):
                if command.startswith('radio '):
                    self.selected=int(command.split()[1]);time.sleep(.0001)
                    return dict(radio=self.selected)
                recorded.append((self.selected,int(command)));return {}
            def close(self):pass
        board=Board(serial='COM3',factory=FakeBridge)
        def run(index):
            for _ in range(50):board.view(index).request(str(index))
        threads=[threading.Thread(target=run,args=(i,)) for i in range(2)]
        for t in threads:t.start()
        for t in threads:t.join(2);self.assertFalse(t.is_alive())
        self.assertEqual(len(recorded),100);self.assertTrue(all(a==b for a,b in recorded))
        board.close()
        with self.assertRaisesRegex(RuntimeError,'closed'):board.view(0).request('0')

    def test_tcp_connections_persist_until_explicit_close(self):
        factory=Mock();board=Board(host='device',factory=factory)
        for index in (0,1,0,1):board.view(index).info()
        self.assertEqual(factory.call_count,2)
        self.assertEqual(factory.call_args_list[0].args[0],'socket://device:1121')
        board.close()

    def test_packet_worker_freezes_payload_and_decodes_received_header(self):
        radio=Radio(Board(serial='COM3',factory=Mock()),0)
        radio.configure=Mock();radio._start=Mock();radio._stop=Mock();radio.write=Mock()
        radio.b=Mock();radio.b.status.side_effect=[dict(decoded=dict(irq_status='0x8'))]+[dict(decoded=dict(irq_status='0x0'))]*100
        payloads={'0203':bytes([3,0]),'010a0003':b'abc','0204':bytes([140,248,138]),'0230':bytes([17])}
        radio.read=lambda command,length:payloads[command]
        radio.packet_start(dict(duration_s=.02,poll_ms=1));radio.job.thread.join(2)
        state=radio.job.snapshot()
        self.assertEqual(state['state'],'complete');self.assertEqual(state['count'],1)
        self.assertEqual(state['results'][0]['payload_hex'],'616263')
        radio.write.assert_any_call('011c01',2)
        self.assertEqual(radio._start.call_count,2);radio._stop.assert_called_once()

    def test_http_validation_and_unknown_routes_do_not_open_device(self):
        factory=Mock();control=Control(Board(serial='COM3',factory=factory))
        server=create_server(control,port=0)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        def error(path,body):
            req=Request(f'http://127.0.0.1:{server.server_port}'+path,data=body,headers={'Content-Type':'application/json'})
            with self.assertRaises(HTTPError) as error:urlopen(req,timeout=2)
            return error.exception.code
        try:
            self.assertEqual(error('/api/v1/radios/0/rx/configure',b'{'),400)
            self.assertEqual(error('/api/v1/radios/0/rx/configure',b'{"frequency_hz":1}'),400)
            self.assertEqual(error('/api/v1/no-such-api',b'{}'),404)
            factory.assert_not_called()
        finally:server.shutdown();worker.join(2);server.server_close();control.close()


if __name__=='__main__':unittest.main()
