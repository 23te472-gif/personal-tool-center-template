import json
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import tkinter as tk

import materials
from app import ToolCenter


class MaterialsTests(unittest.TestCase):
    def test_roundtrip_and_corrupt_config_is_preserved(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'data/materials.json'
            config = materials.load(path)
            config['thesis'] = str(Path(directory) / '论文.doc')
            materials.save(path, config)
            self.assertEqual(materials.load(path), config)
            path.write_text('{', encoding='utf-8')
            with self.assertRaises(ValueError):
                materials.save(path, config)
            self.assertEqual(path.read_text(encoding='utf-8'), '{')

    def test_pack_only_explicit_files_and_reject_missing_selection(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            base = Path(directory)
            thesis = base / '论文.doc'; thesis.write_bytes(b'thesis')
            ppt = base / '汇报.pptx'; ppt.write_bytes(b'slides')
            charts = base / 'charts'; charts.mkdir()
            (charts / 'private.txt').write_text('not selected')
            config = dict(thesis=str(thesis), presentation=str(ppt), charts=str(charts))
            self.assertEqual(materials.pack_files(config), [thesis, ppt])
            ppt.unlink()
            with self.assertRaises(FileNotFoundError):
                materials.pack_files(config)

    def test_ui_starts_without_opening_or_packing_and_blocks_close_when_busy(self):
        class Manager:
            def poll(self): return {}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = tk.Tk(); root.withdraw()
            try:
                with patch('materials_ui.os.startfile', create=True) as opened, patch('materials_ui.create_zip') as packed:
                    app = ToolCenter(root, Path(directory), manager=Manager())
                    root.update_idletasks()
                    opened.assert_not_called(); packed.assert_not_called()
                    self.assertFalse(app.materials.busy)
                    self.assertFalse((Path(directory) / 'data/materials.json').exists())
                    app.materials.busy = True
                    app.close()
                    self.assertTrue(root.winfo_exists())
            finally:
                root.destroy()

    def test_panel_packs_synthetic_files_to_valid_zip(self):
        class Manager:
            def poll(self): return {}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            base = Path(directory)
            thesis = base / '论文.doc'; thesis.write_bytes(b'thesis content')
            ppt = base / '汇报.pptx'; ppt.write_bytes(b'presentation content')
            root = tk.Tk(); root.withdraw()
            try:
                app = ToolCenter(root, base, manager=Manager())
                app.materials.config.update(thesis=str(thesis), presentation=str(ppt))
                app.materials.pack()
                deadline = time.monotonic() + 8
                while app.materials.busy and time.monotonic() < deadline:
                    root.update(); time.sleep(0.02)
                self.assertFalse(app.materials.busy)
                outputs = list((base / '资料打包').glob('*.zip'))
                self.assertEqual(len(outputs), 1)
                with zipfile.ZipFile(outputs[0]) as archive:
                    self.assertIsNone(archive.testzip())
                    self.assertEqual(set(archive.namelist()), {'论文.doc', '汇报.pptx'})
                    self.assertEqual(archive.read('论文.doc'), b'thesis content')
                self.assertEqual(thesis.read_bytes(), b'thesis content')
            finally:
                root.destroy()


if __name__ == '__main__':
    unittest.main()
