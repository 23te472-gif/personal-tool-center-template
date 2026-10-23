import tempfile,unittest
from pathlib import Path
import tkinter as tk
from PIL import Image
from icon_cards import IconCards
from game_icons import find_game_icon

class CardTests(unittest.TestCase):
    def test_selection_check_paging_and_no_overlapping_names(self):
        root=tk.Tk();root.geometry('650x500')
        try:
            changed=[];cards=IconCards(root,checkable=True,on_toggle=lambda key:changed.append(key));cards.pack(fill='both',expand=True)
            items=[dict(id=str(i),name='怪物猎人 · 崛起 Warhammer 40,000',checked=True) for i in range(65)]
            cards.set_items(items);root.update()
            self.assertLessEqual(len(cards.widgets),60)
            cards.select('1');self.assertEqual(cards.selected(),'1');self.assertFalse(changed)
            cards.widgets['1']['check'].invoke();self.assertEqual(changed,['1'])
            first=cards.widgets['0']['frame'];second=cards.widgets['1']['frame']
            self.assertTrue(first.winfo_x()+first.winfo_width()<=second.winfo_x() or first.winfo_y()+first.winfo_height()<=second.winfo_y())
            cards.change_page(1);root.update();self.assertIsNone(cards.selected());self.assertIn('64',cards.widgets)
        finally:root.destroy()
    def test_local_square_icon_preferred_and_bad_appid_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root=Path(folder);cache=root/'appcache/librarycache/123';cache.mkdir(parents=True)
            Image.new('RGB',(600,900),'red').save(cache/'library_600x900.jpg')
            icon=cache/'hash.jpg';Image.new('RGB',(32,32),'green').save(icon)
            self.assertEqual(find_game_icon('123',[root]),icon)
            self.assertIsNone(find_game_icon('../123',[root]))

if __name__=='__main__':unittest.main()
