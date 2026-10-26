"""Personal Tool Center 2: local WebView frontend and existing-tool adapters."""
from pathlib import Path
from logging.handlers import RotatingFileHandler
import argparse,ctypes,json,logging,os,sys,tempfile,threading,time,traceback

BASE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
if '--check' in sys.argv:
    import runpy
    runpy.run_path(str(BASE.parents[1]/'check.py'),run_name='__main__')
    raise SystemExit(0)

sys.dont_write_bytecode=True

def configure_logs(base):
    folder=Path(base)/'logs';folder.mkdir(parents=True,exist_ok=True)
    handler=RotatingFileHandler(folder/'app.log',maxBytes=1_000_000,backupCount=3,encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    logging.getLogger().setLevel(logging.INFO);logging.getLogger().addHandler(handler)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ui-smoke',action='store_true');parser.add_argument('--smoke-result');args=parser.parse_args()
    configure_logs(BASE)
    from backend import Bridge
    from singleton import SingleInstance
    import webview
    from bridge_boundary import install_boundary
    install_boundary()
    holder={};ready=threading.Event()
    def show_existing():
        if ready.wait(10):
            try:holder['window'].restore();holder['window'].show()
            except Exception:logging.getLogger('toolcenter').exception('Restore window failed')
    session=SingleInstance(BASE,show_existing)
    temp=None
    try:
        if not args.ui_smoke and not session.acquire():return
        entry=BASE/'frontend/dist/index.html'
        if not entry.is_file():raise RuntimeError('前端尚未构建，请运行前端构建后再启动。')
        if args.ui_smoke:
            temp=tempfile.TemporaryDirectory(prefix='ui-smoke-',dir=BASE/'tests')
            root=Path(temp.name);fake=root/'outputs';testbase=fake/'个人工具中心新版';testbase.mkdir(parents=True)
            (fake/'个人工具中心/data').mkdir(parents=True);(fake/'游戏管家/data').mkdir(parents=True)
            bridge=Bridge(testbase,fake,opener=lambda value:None)
        else:bridge=Bridge(BASE)
        native=webview.create_window('个人工具中心 · 2.0',url=str(entry),width=1180,height=820,min_size=(900,640),background_color='#F5F7FA',text_select=True)
        native.expose(bridge.call)
        bridge._window=native;holder['window']=native
        native.events.shown+=lambda:ready.set()
        def closing():
            if bridge._busy():
                ctypes.windll.user32.MessageBoxW(0,'打包任务正在进行，请完成后再关闭工具中心。','任务尚未完成',0x40);return False
            return True
        native.events.closing+=closing
        def smoke():
            output=Path(args.smoke_result or BASE/'tests/ui-smoke-result.json')
            try:
                native.events.loaded.wait(25)
                time.sleep(1)
                done=threading.Event();box={}
                def received(value):box['value']=value;done.set()
                native.evaluate_js("(async()=>{const r=await window.pywebview.api.call('bootstrap',{});return {bridge:r.ok,version:r.data?.app?.version,title:document.title,body:document.body.innerText.slice(0,12000),rootChildren:document.querySelector('#root')?.childElementCount||0}})()",callback=received)
                if not done.wait(15):raise RuntimeError('前端接口没有返回结果')
                value=box['value']
                output.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
            except Exception as exc:output.write_text(json.dumps(dict(error=str(exc))),encoding='utf-8')
            finally:native.destroy()
        profile=(Path(temp.name)/'webview') if args.ui_smoke else BASE/'data/webview'
        try:webview.start(smoke if args.ui_smoke else None,gui='edgechromium',debug=False,private_mode=True,storage_path=str(profile),localization={'global.quitConfirmation':'是否关闭工具中心？'})
        finally:bridge._shutdown()
    finally:
        session.close()
        if temp:temp.cleanup()

if __name__=='__main__':
    try:main()
    except Exception:
        logging.getLogger('toolcenter').exception('Startup failed')
        if sys.stderr is not None:traceback.print_exc()
        if '--ui-smoke' not in sys.argv:ctypes.windll.user32.MessageBoxW(0,'工具中心启动未完成，请查看新版目录 logs/app.log。请确认已安装依赖并完成前端构建。','启动失败',0x10)
        raise SystemExit(1)
