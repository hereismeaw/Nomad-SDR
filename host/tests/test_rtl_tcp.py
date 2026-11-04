# SPDX-License-Identifier: GPL-3.0-only
import io
import socket
import struct
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import zlib
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge import BridgeError
from nomad_rx import HEADER,read_frame
from nomad_rtl_tcp import COMMAND,DONGLE_HEADER,ClientSession,Interpolator,Settings,unsigned_iq,serve

def compact_frame(sequence=0,shift=6,kind=1):
    payload=bytes([shift])+bytes([64,192])*125 if kind==1 else struct.pack('<9I',sequence,sequence,0,0,0,16000000,0,0,0)
    head=HEADER.pack(b'LIQ8',1,kind,0,3,sequence,sequence*125,125 if kind==1 else 0,len(payload),62500,0,zlib.crc32(payload),0)
    return head[:40]+struct.pack('<I',zlib.crc32(head[:40]))+payload

class RTLTests(unittest.TestCase):
    def test_compact_scale_sign_and_terminal(self):
        data,end=read_frame(io.BytesIO(compact_frame()),3,62500,0,compact=True)
        self.assertIsNone(end)
        np.testing.assert_array_equal(np.frombuffer(data,dtype='<c8'),np.full(125,(64-64j)*2**-16))
        data,end=read_frame(io.BytesIO(compact_frame(sequence=1,kind=2)),3,62500,1,compact=True)
        self.assertIsNone(data);self.assertEqual(end['sent'],1)
    def test_compact_bad_scale_crc_magic(self):
        with self.assertRaisesRegex(BridgeError,'scale'):read_frame(io.BytesIO(compact_frame(shift=17)),3,62500,0,compact=True)
        wire=bytearray(compact_frame());wire[-1]^=1
        with self.assertRaisesRegex(BridgeError,'CRC'):read_frame(io.BytesIO(wire),3,62500,0,compact=True)
        with self.assertRaisesRegex(BridgeError,'header'):read_frame(io.BytesIO(compact_frame()),3,62500,0)
    def test_rtl_header_and_unsigned_iq(self):
        self.assertEqual(DONGLE_HEADER,b'RTL0'+bytes(8))
        self.assertEqual(unsigned_iq(np.array([0j,1-1j,2-2j]),0),bytes([128,128,255,0,255,0]))
    def test_resampler_continuity_rate_and_frequency(self):
        samples=np.exp(2j*np.pi*5000*np.arange(125*40)/62500)
        whole=Interpolator(250000).process(samples);split=Interpolator(250000)
        joined=np.concatenate([split.process(samples[i:i+125]) for i in range(0,len(samples),125)])
        np.testing.assert_allclose(whole,joined,atol=1e-12)
        self.assertEqual(len(joined),4*len(samples))
        phase=np.angle(joined[1001:]*np.conj(joined[1000:-1]))
        self.assertAlmostEqual(np.mean(phase)*250000/(2*np.pi),5000,delta=2)
        self.assertGreater(np.mean(np.abs(joined[1000:])),.98)
    def test_controls_and_signed_ppm(self):
        with socket.socket() as sock:
            session=ClientSession(sock,'host',0,915000000,250000,60)
            session.apply_command(1,2440000000);session.apply_command(5,(-10)&0xffffffff)
            self.assertEqual(session.settings.corrected_frequency,2439975600)
            with self.assertRaises(ValueError):session.apply_command(1,100000000)
            with self.assertRaises(ValueError):session.apply_command(2,2400000)
    def test_gui_accepts_full_synthesizer_range(self):
        with socket.socket() as sock:
            session=ClientSession(sock,'host',0,915000000,250000,60)
            for frequency in (150000000,433000000,1090000000,1550000000,2200000000,2500000000):
                session.apply_command(1,frequency)
                self.assertEqual(session.settings.frequency,frequency)
            for frequency in (149999999,2500000001):
                with self.assertRaises(ValueError):session.apply_command(1,frequency)
    def test_fragmented_commands(self):
        left,right=socket.socketpair()
        try:
            left.settimeout(.1);session=ClientSession(left,'host',0,915000000,250000,60)
            thread=threading.Thread(target=session.read_commands);thread.start()
            wire=COMMAND.pack(1,2440000000)+COMMAND.pack(2,62500)
            right.sendall(wire[:2]);right.sendall(wire[2:7]);right.sendall(wire[7:])
            right.shutdown(socket.SHUT_WR);thread.join(2)
            self.assertFalse(thread.is_alive());self.assertEqual(session.snapshot()[0],Settings(2440000000,62500))
        finally:left.close();right.close()
    def test_loopback_reconnect_header_and_control(self):
        ready=threading.Event();stop=threading.Event();ports=[];received=[]
        def on_ready(port):ports.append(port);ready.set()
        def fake_run(session):
            session.client.sendall(DONGLE_HEADER);data=bytearray()
            while len(data)<5:data.extend(session.client.recv(5-len(data)))
            received.append(COMMAND.unpack(data));session.client.close()
        with patch.object(ClientSession,'run',fake_run):
            thread=threading.Thread(target=serve,kwargs=dict(port=0,ready=on_ready,stop=stop));thread.start()
            self.assertTrue(ready.wait(2))
            try:
                for freq in (915000000,2440000000):
                    with socket.create_connection(('127.0.0.1',ports[0]),timeout=2) as s:
                        header=bytearray()
                        while len(header)<12:header.extend(s.recv(12-len(header)))
                        self.assertEqual(header,DONGLE_HEADER);s.sendall(COMMAND.pack(1,freq))
                limit=time.monotonic()+2
                while len(received)<2 and time.monotonic()<limit:time.sleep(.01)
            finally:stop.set();thread.join(2)
        self.assertEqual(received,[(1,915000000),(1,2440000000)])

if __name__=='__main__':unittest.main()
