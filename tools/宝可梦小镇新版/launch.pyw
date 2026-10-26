from pathlib import Path
import runpy,sys
sys.dont_write_bytecode=True
runpy.run_path(str(Path(__file__).with_name('app.py')),run_name='__main__')
