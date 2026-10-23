from pathlib import Path
import sys,unittest,tempfile
from PIL import Image
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import backend
from local_icons import SteamIcons
class LocalIconTests(unittest.TestCase):
    def test_only_numeric_appids_and_bounded_local_png(self):
        cache=SteamIcons(roots=[])
        self.assertEqual(cache.get('https://example.com/pixel'),'')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            icon=Path(folder)/'synthetic.png';Image.new('RGBA',(24,24),(40,90,120,255)).save(icon)
            self.check_image(cache,icon)
    def check_image(self,cache,icon):
        with patch('local_icons.game_icons.find_game_icon',return_value=icon) as find:
            value=cache.get('548430');self.assertTrue(value.startswith('data:image/png;base64,'))
            self.assertLess(len(value),90000);self.assertEqual(cache.get('548430'),value);find.assert_called_once()
if __name__=='__main__':unittest.main()
