from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from PIL import Image
from win_icons import shortcut_image

class IconPreviewTests(unittest.TestCase):
    def test_configured_ico_preferred_over_stale_shell_cache(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            icon=Path(folder)/'伙伴.ico'
            Image.new('RGBA',(64,64),(15,120,190,255)).save(icon,format='ICO')
            with patch('win_icons.shell_image') as shell:
                value=shortcut_image(dict(path='C:/example.lnk',icon=str(icon)+',0'),48)
                self.assertEqual(value.size,(48,48));self.assertEqual(value.getpixel((24,24)),(15,120,190,255))
                shell.assert_not_called()
    def test_exe_resource_and_missing_ico_fall_back(self):
        with patch('win_icons.shell_image',return_value='fallback') as shell:
            for icon in ('app.exe,0','C:/missing.ico,0',',0'):
                self.assertEqual(shortcut_image(dict(path='C:/example.lnk',icon=icon),48),'fallback')
            self.assertEqual(shell.call_count,3)
