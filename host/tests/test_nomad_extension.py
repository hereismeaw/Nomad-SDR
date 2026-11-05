# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nomad_extension_probe as probe


class ExtensionProbeTests(unittest.TestCase):
    def test_prepare_requires_callback_verification_before_io(self):
        b=Mock()
        with self.assertRaisesRegex(RuntimeError,'verification'):
            probe.prepare_packed(b,915000000,62500,dict(success=True,version=probe.extension.APP))
        b.read_command.assert_not_called()

    def test_prepare_rejects_different_chip_before_receiver_setup(self):
        b=Mock()
        b._payload.return_value=bytes.fromhex('0102030405060708')
        verified=dict(success=True,version=probe.extension.APP,marker='0x49515033',
                      fifo_marker='0x46494631',callback_restored=True,uid='0000000000000000')
        with patch.object(probe,'NomadReceiver') as receiver:
            with self.assertRaisesRegex(RuntimeError,'different chip'):
                probe.prepare_packed(b,915000000,62500,verified)
            receiver.assert_not_called()

    def test_signed_extremes_reference_bytes(self):
        values = [-4194304, 4194303, -32768, 32767, -1, 0]
        self.assertEqual(probe.expected_packing(values, 8, 15), bytes([128,127,255,0,255,0]))
        self.assertEqual(probe.expected_packing(values, 12, 12), bytes.fromhex('00fc3ff87f00ff0f00'))

    def test_ram_writes_split_into_guarded_64_word_commands(self):
        b = Mock()
        b.status.return_value = {'decoded': {'cmd_status': 2}}
        probe.write_words(b, 0x806000, range(130))
        commands = [call.args[0] for call in b.write_command.call_args_list]
        self.assertEqual([len(command) for command in commands], [262,262,14])
        self.assertEqual([command[:2].hex() for command in commands], ['0105']*3)
        self.assertEqual([int.from_bytes(command[2:6], 'big') for command in commands],
                         [0x806000,0x806100,0x806200])
        self.assertEqual(commands[-1][6:], bytes.fromhex('0000008000000081'))

    def test_out_of_range_ram_write_never_sends_command(self):
        b = Mock()
        for address, values in ((0x7ffffc,[1]),(0x80fffc,[1,2]),(0x806001,[1]),(0x806000,[])):
            with self.assertRaises(ValueError):
                probe.write_words(b, address, values)
        b.write_command.assert_not_called()

    def test_mismatched_chip_binding_never_invokes_extension(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            verification = base/'verify.json'
            verification.write_text(json.dumps(dict(success=True,version=probe.extension.APP,uid='0000000000000000')))
            b = Mock()
            b.info.return_value = dict(board='radiomaster-nomad',radio=1)
            b.version.return_value = dict(data=probe.extension.APP)
            b._payload.return_value = bytes.fromhex('0102030405060708')
            bridge = Mock()
            bridge.__enter__ = Mock(return_value=b)
            bridge.__exit__ = Mock(return_value=False)
            argv = ['probe','--radio','1','--verification',str(verification),'--out',str(base/'result')]
            with patch.object(sys,'argv',argv), patch.object(probe,'Bridge',return_value=bridge), patch.object(probe,'vector_test') as vectors:
                with self.assertRaisesRegex(RuntimeError,'different chip'):
                    probe.main()
                vectors.assert_not_called()
            result = json.loads((base/'result/probe.json').read_text())
            self.assertFalse(result['complete'])
            self.assertEqual(result['version_after'],probe.extension.APP)


if __name__ == '__main__':
    unittest.main()
