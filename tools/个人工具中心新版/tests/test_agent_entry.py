from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import Bridge

class AgentEntryTests(unittest.TestCase):
    def test_replaces_legacy_entry_and_preserves_existing_tools(self):
        bridge=Bridge(opener=lambda path:None)
        try:
            specs=bridge._tool_specs();ids={s.id for s in specs}
            self.assertIn('agent',ids);self.assertNotIn('legacy',ids)
            self.assertTrue({'town','status','icons'}.issubset(ids))
            self.assertFalse({'games','delivery'} & ids)
            agent=next(s for s in specs if s.id=='agent')
            self.assertEqual(agent.script.name,'app.py');self.assertEqual(agent.title,'Agent 工作台')
            self.assertEqual(agent.script.parent.name,'agent-workbench') # optional adjacent repository
        finally:bridge._shutdown()
