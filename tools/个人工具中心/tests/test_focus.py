import tempfile, unittest
from pathlib import Path
from focus_model import FocusSession, default_focus, validate_focus
from playful_store import load_json, save_json

class FocusTests(unittest.TestCase):
    def test_pause_reward_once_and_restore(self):
        now=[0.0]; session=FocusSession(default_focus(), lambda:now[0])
        self.assertEqual(session.remaining,1500)
        session.start('论文',5);now[0]=100;session.pause()
        self.assertEqual(session.remaining,200)
        now[0]=1000;self.assertEqual(session.remaining,200)
        restored=FocusSession(session.snapshot(),lambda:now[0])
        self.assertFalse(restored.running);restored.resume();now[0]+=200
        self.assertTrue(restored.tick());self.assertEqual(restored.berries,1)
        self.assertFalse(restored.tick());self.assertEqual(restored.berries,1)
        restored.start('提前结束',15);restored.finish_early();self.assertEqual(restored.berries,1)
        with self.assertRaises(ValueError):restored.start('无效',0)

    def test_shop_and_atomic_corrupt_preservation(self):
        data=default_focus();data['berries']=5;session=FocusSession(data)
        session.buy('盆栽');self.assertEqual(session.berries,3)
        session.buy('盆栽');self.assertEqual(session.berries,3)
        with self.assertRaises(ValueError):session.buy('书架')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path=Path(folder)/'focus.json'
            save_json(path,session.snapshot(),default_focus(),validate_focus)
            self.assertEqual(load_json(path,default_focus(),validate_focus)['berries'],3)
            path.write_text('{',encoding='utf-8')
            with self.assertRaises(ValueError):save_json(path,default_focus(),default_focus(),validate_focus)
            self.assertEqual(path.read_text(),'{')
        data=default_focus();data['berries']=-1
        with self.assertRaises(ValueError):validate_focus(data)

if __name__=='__main__':unittest.main()
