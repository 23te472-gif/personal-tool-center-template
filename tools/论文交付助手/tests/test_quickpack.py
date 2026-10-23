import unittest,tempfile,zipfile
from pathlib import Path
from unittest.mock import patch
from quickpack import create_zip

class ZipTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)
    def test_only_selected_files_empty_allowed_duplicate_names(self):
        a=self.base/'a';b=self.base/'b';a.mkdir();b.mkdir();(a/'论文.doc').write_bytes(b'one');(b/'论文.doc').write_bytes(b'')
        out=create_zip([a/'论文.doc',b/'论文.doc',a/'论文.doc'],self.base/'out',lambda _:None)
        with zipfile.ZipFile(out) as z:
            self.assertEqual(z.namelist(),['论文.doc','论文 (2).doc']);self.assertEqual(z.read('论文.doc'),b'one');self.assertEqual(z.read('论文 (2).doc'),b'')
        self.assertEqual((a/'论文.doc').read_bytes(),b'one')
    def test_missing_and_source_change_do_not_publish(self):
        with self.assertRaises(ValueError):create_zip([self.base/'missing'],self.base/'out',lambda _:None)
        p=self.base/'a.txt';p.write_bytes(b'original')
        with self.assertRaises(OSError):create_zip([p],self.base/'out',lambda _:p.write_bytes(b'changed'))
        self.assertEqual(list((self.base/'out').iterdir()),[])
    def test_publish_failure_cleanup(self):
        p=self.base/'a.txt';p.write_bytes(b'a')
        with patch('quickpack.os.rename',side_effect=OSError('disk')):
            with self.assertRaises(OSError):create_zip([p],self.base/'out',lambda _:None)
        self.assertEqual(list((self.base/'out').iterdir()),[])

if __name__=='__main__':unittest.main()
