import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch,Mock
from center import tools_for,ToolManager,WindowsWindows,load_recent,save_recent

class FakeWindows:
    found=None
    def find(self,title,pid=None):return self.found
    def focus(self,hwnd):return True
class FakeProcess:
    pid=123
    code=None
    def poll(self):return self.code

class CenterTests(unittest.TestCase):
    def test_same_title_launcher_console_is_not_an_existing_app(self):
        windows=WindowsWindows.__new__(WindowsWindows);windows.api=Mock()
        windows.api.FindWindowW.side_effect=lambda cls,title:99 if cls is None else 0
        windows.api.IsWindow.return_value=True
        self.assertIsNone(windows.find('个人工具中心'))
    def test_native_status_card_window_is_still_found(self):
        windows=WindowsWindows.__new__(WindowsWindows);windows.api=Mock()
        windows.api.FindWindowW.side_effect=lambda cls,title:88 if cls=='CodexDesktopStatusCardNative' else 0
        windows.api.IsWindow.return_value=True
        self.assertEqual(windows.find('桌面状态卡片'),88)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)/'中心';self.base.mkdir()
        self.tools=tools_for(self.base);self.tool=self.tools[0]
        self.tool.script.parent.mkdir();self.tool.script.write_text('print(1)')
        self.windows=FakeWindows();self.proc=FakeProcess();self.calls=[]
        def spawn(*args,**kwargs):self.calls.append((args,kwargs));return self.proc
        self.manager=ToolManager(self.base,self.tools,self.windows,spawn)
    def test_relative_paths(self):
        self.assertEqual([tool.id for tool in self.tools],['games','delivery','town','status']);self.assertEqual(self.tool.script.parent.parent,self.base.parent)
    def test_native_executable_launches_directly(self):
        native=next(t for t in self.tools if t.id=='status');native.script.parent.mkdir();native.script.write_bytes(b'fake executable')
        self.manager.open('status');args,kwargs=self.calls[0]
        self.assertEqual(args[0],[str(native.script)]);self.assertFalse(kwargs.get('shell',False))
    def test_launch_and_pending_no_duplicate(self):
        self.assertEqual(self.manager.open(self.tool.id)['action'],'started')
        self.assertEqual(self.manager.open(self.tool.id)['action'],'pending');self.assertEqual(len(self.calls),1)
        args,kwargs=self.calls[0];self.assertEqual(Path(args[0][1]),self.tool.script);self.assertFalse(kwargs.get('shell',False))
        self.windows.found=77;self.assertEqual(self.manager.open(self.tool.id)['action'],'focused');self.assertEqual(len(self.calls),1)
    def test_already_open_and_missing(self):
        self.windows.found=77;self.assertEqual(self.manager.open(self.tool.id)['action'],'focused');self.assertEqual(len(self.calls),0)
        self.windows.found=None;self.tool.script.unlink()
        with self.assertRaises(FileNotFoundError):self.manager.open(self.tool.id)
    def test_nonzero_exit_logs_and_can_retry(self):
        self.manager.open(self.tool.id);self.proc.code=1
        updates=self.manager.poll();self.assertEqual(updates[self.tool.id]['state'],'failed');self.assertIn('日志',updates[self.tool.id]['message'])
        self.proc=FakeProcess();self.manager.open(self.tool.id);self.assertEqual(len(self.calls),2)
    def test_recent_atomic_and_corruption(self):
        p=self.base/'recent.json';save_recent(p,{'games':'2026-10-19T12:00:00'});before=p.read_bytes()
        with patch('center.os.replace',side_effect=OSError('disk')):
            with self.assertRaises(OSError):save_recent(p,{'games':'2026-10-20T12:00:00'})
        self.assertEqual(p.read_bytes(),before);self.assertEqual(load_recent(p)['games'],'2026-10-19T12:00:00')
        p.write_text('{')
        with self.assertRaises(ValueError):load_recent(p)
    def test_popen_failure_not_running(self):
        self.manager.spawn=lambda *a,**k:(_ for _ in ()).throw(OSError('denied'))
        with self.assertRaises(OSError):self.manager.open(self.tool.id)
        self.assertEqual(self.manager.poll()[self.tool.id]['state'],'idle')
    def test_failed_log_reads_tail_once_and_releases_process(self):
        self.manager.open(self.tool.id);log=self.manager.logs[self.tool.id];log.write_bytes(b'x'*100000+b'FINAL ERROR')
        self.proc.code=1
        with patch.object(Path,'read_bytes',side_effect=AssertionError('must not read whole log')):
            first=self.manager.poll()[self.tool.id];second=self.manager.poll()[self.tool.id]
        self.assertIn('FINAL ERROR',first['message']);self.assertEqual(first,second)
        self.assertNotIn(self.tool.id,self.manager.processes)

if __name__=='__main__':unittest.main()
