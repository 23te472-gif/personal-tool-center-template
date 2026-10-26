import unittest
from pathlib import Path
from library import Game
from app import filter_games, TaskState, confirm_candidate
from discovery import Candidate

class AppTests(unittest.TestCase):
    def test_search_name_and_notes(self):
        games=[Game('a','Hades',notes='冥界'),Game('b','雨中冒险')]
        self.assertEqual(filter_games(games,'冥界'),[games[0]])
        self.assertEqual(filter_games(games,'HADES'),[games[0]])

    def test_confirm_is_explicit(self):
        c=Candidate('Hades','C:/h.exe','工具')
        self.assertIsNone(confirm_candidate(c,False))
        g=confirm_candidate(c,True)
        self.assertEqual(g.tool_paths,['C:/h.exe']); self.assertEqual(g.save_dir,'')

    def test_busy_error_and_close(self):
        state=TaskState(); state.start()
        self.assertFalse(state.can_close)
        with self.assertRaises(RuntimeError): state.start()
        state.finish(False,'磁盘不足')
        self.assertTrue(state.can_close); self.assertEqual(state.message,'磁盘不足')
