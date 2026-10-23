from pathlib import Path
import sys,tempfile,time,unittest,socket,json
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from singleton import SingleInstance

class SingletonTests(unittest.TestCase):
    def test_invalid_json_shapes_do_not_stop_listener(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            callback=Mock();first=SingleInstance(folder,callback);second=SingleInstance(folder,Mock())
            try:
                self.assertTrue(first.acquire())
                for payload in (b'null',b'[]',b'42',b'"hello"',b'{',b'{"action":"show","token":"bad"}'):
                    with socket.create_connection(first.socket.getsockname(),timeout=1) as conn:
                        conn.settimeout(1);conn.sendall(payload);conn.shutdown(socket.SHUT_WR)
                        self.assertEqual(conn.recv(1024),b'')
                callback.assert_not_called();self.assertFalse(second.acquire())
                deadline=time.monotonic()+1
                while not callback.called and time.monotonic()<deadline:time.sleep(.01)
                callback.assert_called_once()
            finally:second.close();first.close()
    def test_second_instance_restores_first_without_new_server(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            callback=Mock();first=SingleInstance(folder,callback);second=SingleInstance(folder,Mock())
            try:
                self.assertTrue(first.acquire());self.assertFalse(second.acquire())
                deadline=time.monotonic()+1
                while not callback.called and time.monotonic()<deadline:time.sleep(.01)
                callback.assert_called_once();self.assertIsNone(second.socket)
            finally:second.close();first.close()

if __name__=='__main__':unittest.main()
