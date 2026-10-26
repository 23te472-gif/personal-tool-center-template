from pathlib import Path
import sys,unittest,tempfile
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import backend
from local_icons import SteamIcons
class LocalIconTests(unittest.TestCase):
    def test_only_numeric_appids_and_bounded_local_png(self):
        cache=SteamIcons(roots=[])
        self.assertEqual(cache.get('https://example.com/pixel'),'')
        with tempfile.TemporaryDirectory() as temp:
            icon=Path(temp)/'generic.png';Image.new('RGBA',(40,40),'#437baa').save(icon)
            with patch('local_icons.game_icons.find_game_icon',return_value=icon) as find:
                value=cache.get('548430');self.assertTrue(value.startswith('data:image/png;base64,'))
                self.assertLess(len(value),90000);self.assertEqual(cache.get('548430'),value);find.assert_called_once()
