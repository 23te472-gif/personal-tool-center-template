from pathlib import Path
from unittest.mock import Mock
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pet_launcher import PetLauncher

class PetLauncherTests(unittest.TestCase):
    def test_explicit_launch_uses_configured_entry_and_limits_double_click(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=root/'pet.lnk';entry.write_bytes(b'fixture');opener=Mock()
            launcher=PetLauncher(root/'data/pet_launcher.json',opener,desktop=root/'empty')
            self.assertTrue(launcher.launch()['needs_configuration']);opener.assert_not_called()
            launcher.configure(entry);self.assertEqual(launcher.launch()['action'],'requested')
            self.assertEqual(launcher.launch()['action'],'pending');opener.assert_called_once_with(str(entry.resolve()))
            other=PetLauncher(root/'data/pet_launcher.json',opener,desktop=root/'empty')
            self.assertEqual(other.entry(),entry.resolve())
    def test_missing_or_invalid_path_does_not_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);opener=Mock();launcher=PetLauncher(root/'config.json',opener,desktop=root/'empty')
            for entry in (root/'missing.exe',root/'bad.txt'):
                with self.assertRaises(ValueError):launcher.configure(entry)
            opener.assert_not_called()
