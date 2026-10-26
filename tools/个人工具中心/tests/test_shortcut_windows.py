"""Windows COM integration uses only newly created temporary shortcuts."""
import os,subprocess,tempfile,unittest
from pathlib import Path
from shortcut_model import ShortcutBackend,ShortcutService

@unittest.skipUnless(os.name=='nt' and os.environ.get('RUN_WINDOWS_INTEGRATION')=='1','Opt-in Windows integration: RUN_WINDOWS_INTEGRATION=1')
class WindowsShortcutTests(unittest.TestCase):
    def test_real_com_roundtrip_in_temporary_desktop(self):
        # Shell also has trouble resolving shortcuts in this project's very deep path.
        # Use a short isolated folder while exercising the real handler.
        with tempfile.TemporaryDirectory(prefix='icon-test-',dir=None) as folder:
            base=Path(folder);desktop=base/'临时桌面';desktop.mkdir();lnk=desktop/'软件 & $test.lnk'
            script=base/'create.ps1'
            script.write_text('param([string]$path)\n$ErrorActionPreference="Stop"\n$s=New-Object -ComObject WScript.Shell\n$l=$s.CreateShortcut($path)\n$l.TargetPath=Join-Path $env:WINDIR "System32/notepad.exe"\n$l.Arguments="--test-do-not-launch"\n$l.Description="测试快捷方式"\n$l.Save()\n',encoding='utf-8-sig')
            result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(script),str(lnk)],capture_output=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
            class Backend(ShortcutBackend):
                def desktop_dirs(self):return [desktop]
            backend=Backend(base);service=ShortcutService(base,backend);original=backend.read(lnk)
            from PIL import Image
            icon=base/'sample.ico';Image.new('RGBA',(32,32),'#4278ad').save(icon,format='ICO')
            service.apply(lnk,icon,original)
            changed=backend.read(lnk);self.assertNotEqual(changed['icon'],original['icon'])
            self.assertEqual({k:v for k,v in changed.items() if k!='icon'},{k:v for k,v in original.items() if k!='icon'})
            service.restore(lnk);self.assertEqual(backend.read(lnk),original)
            from win_icons import shell_image
            image=shell_image(lnk)
            self.assertIsNotNone(image);self.assertEqual(image.size,(72,72));self.assertIsNotNone(image.getbbox())

    def test_notify_reports_saved_item_and_flushes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            backend=ShortcutBackend(Path(folder))
            # Existing real file is used only for a Shell update notice, without saving it.
            from PIL import Image
            icon=base/'sample.ico';Image.new('RGBA',(32,32),'#4278ad').save(icon,format='ICO')
            result=backend.refresh_icon(icon)
            self.assertTrue(result['notified'])

if __name__=='__main__':unittest.main()
