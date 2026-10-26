from pathlib import Path
import subprocess,sys
base=Path(__file__).resolve().parent
for relative in ['tools/'+n+'/tests' for n in ('个人工具中心新版','个人工具中心','游戏管家','宝可梦小镇新版')]:
    tests=base/relative
    result=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(tests),'-p','test_*.py'],cwd=tests.parent)
    if result.returncode:raise SystemExit(result.returncode)
print('All Python suites passed. Frontend tests: npm test in each frontend directory.')
