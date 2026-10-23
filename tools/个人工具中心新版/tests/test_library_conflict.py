from pathlib import Path
import sys,tempfile,unittest
from dataclasses import replace
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'游戏管家'))
from library import Game,load_library,save_library,library_revision

class LibraryConflictTests(unittest.TestCase):
    def test_stale_session_cannot_overwrite_new_game_or_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'library.json';save_library(path,[Game('1','原名')])
            old=load_library(path);new=load_library(path)
            new[0].favorite=True;new.append(Game('2','新游戏'));save_library(path,new)
            old[0].notes='旧窗口备注'
            with self.assertRaisesRegex(ValueError,'其他窗口'):save_library(path,old)
            saved=load_library(path);self.assertEqual(len(saved),2);self.assertTrue(saved[0].favorite)
    def test_explicit_revision_rejects_new_list_from_old_app(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'library.json';save_library(path,[Game('1','原名')])
            old=load_library(path);revision=library_revision(path)
            new=load_library(path);new[0].name='新版改名';save_library(path,new)
            with self.assertRaises(ValueError):save_library(path,[replace(old[0],notes='旧改动')],expected_revision=revision)
            self.assertEqual(load_library(path)[0].name,'新版改名')
