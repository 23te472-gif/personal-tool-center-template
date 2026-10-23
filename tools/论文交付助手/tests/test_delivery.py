import unittest,tempfile,json,zipfile,hashlib
from pathlib import Path
from unittest.mock import patch
from delivery import Project,Material,load_project,save_project,check_project,build_delivery,history

class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.output=self.root/'out'
        self.file=self.root/'论文.docx';self.file.write_bytes(b'paper content')
        self.project=Project('毕业论文','论文提交',str(self.output),False,[Material(str(self.file),'论文')],'本次备注')
    def test_storage(self):
        p=self.root/'project.json';save_project(p,self.project);self.assertEqual(load_project(p),self.project)
        original=p.read_bytes()
        with patch('delivery.os.replace',side_effect=OSError('disk')):
            with self.assertRaises(OSError):save_project(p,self.project)
        self.assertEqual(p.read_bytes(),original)
        p.write_text('{')
        with self.assertRaises(ValueError):load_project(p)
    def test_required_and_pdf(self):
        self.project.scene='最终答辩';self.assertTrue(check_project(self.project)['errors'])
        self.project.scene='论文提交';self.project.require_pdf=True
        self.assertTrue(any('PDF' in x for x in check_project(self.project)['errors']))
    def test_missing_empty_and_duplicate_paths(self):
        self.project.materials=[Material(str(self.root/'missing'),'论文')]
        self.assertTrue(check_project(self.project)['errors'])
        self.file.write_bytes(b'');self.project.materials=[Material(str(self.file),'论文')]
        self.assertTrue(check_project(self.project)['errors'])
        self.file.write_bytes(b'a');self.project.materials*=2
        self.assertTrue(check_project(self.project)['errors'])
    def test_build_zip_and_history(self):
        result=build_delivery(self.project,lambda _:None)
        manifest=json.loads((result/'交付记录.json').read_text(encoding='utf-8'))
        with zipfile.ZipFile(result/'交付包.zip') as z:
            data=z.read('论文/论文.docx');self.assertEqual(data,self.file.read_bytes())
            self.assertEqual(manifest['files'][0]['sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(len(history(self.output)),1)
        self.assertEqual(self.file.read_bytes(),b'paper content')
    def test_same_names_numbered_and_warned(self):
        other=self.root/'nested';other.mkdir();(other/self.file.name).write_bytes(b'other')
        self.project.materials.append(Material(str(other/self.file.name),'论文'))
        check=check_project(self.project);self.assertTrue(check['warnings']);self.assertFalse(check['errors'])
        result=build_delivery(self.project,lambda _:None)
        self.assertEqual(len(list((result/'交付文件/论文').iterdir())),2)
    def test_source_changes_and_failure_cleanup(self):
        def mutate(message):self.file.write_bytes(b'changed')
        with self.assertRaises(OSError):build_delivery(self.project,mutate)
        self.assertEqual(list(self.output.iterdir()),[])
        with patch('delivery.os.replace',side_effect=OSError('disk')):
            with self.assertRaises(OSError):build_delivery(self.project,lambda _:None)
        self.assertEqual(list(self.output.iterdir()),[])
    def test_reject_source_parent_and_bad_name(self):
        self.project.name='../escape';self.assertTrue(check_project(self.project)['errors'])
        self.project.name='毕业论文';self.project.output=str(self.file)
        self.assertTrue(check_project(self.project)['errors'])
    def test_late_mutation_and_selection(self):
        second=self.root/'图.png';second.write_bytes(b'figure')
        self.project.materials.append(Material(str(second),'附件'))
        calls=[]
        def mutate(m):
            calls.append(m)
            if len(calls)==2:self.file.write_bytes(b'changed late')
        with self.assertRaises(OSError):build_delivery(self.project,mutate)
        self.project.materials=[Material(str(self.file),'论文',False)]
        self.assertTrue(check_project(self.project)['errors'])

    def test_change_between_check_and_copy(self):
        actual_check=check_project
        def changed(project):
            result=actual_check(project);self.file.write_bytes(b'changed after check');return result
        with patch('delivery.check_project',side_effect=changed):
            with self.assertRaises(OSError):build_delivery(self.project,lambda _:None)

if __name__=='__main__':unittest.main()
