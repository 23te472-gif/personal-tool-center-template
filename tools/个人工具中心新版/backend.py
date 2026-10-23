"""Whitelisted local bridge. No arbitrary shell/URL/file-opening interface."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json,logging,os,re,sys,threading,time,uuid
import store

SOURCE=Path(__file__).resolve().parent
for folder in (SOURCE.parent/'游戏管家',SOURCE.parent/'个人工具中心'):
    if str(folder) not in sys.path:sys.path.insert(0,str(folder))
import center as old_center
import materials,quickpack,playful_store,wheel_model,wheel_steam
import library as game_library
import trainers
from local_icons import SteamIcons
from integrated_windows import IntegratedWindows

MATERIAL_NAMES={'thesis':'论文','presentation':'汇报 PPT','charts':'图表与数据'}
CHALLENGES=('先玩20分钟，再决定是否继续。','试试一个平时少用的角色或玩法。','这次以轻松体验为主。','给自己设一个小目标，完成就休息。')

class Bridge:
    def __init__(self,base=SOURCE,legacy_root=None,opener=None):
        self._base=Path(base);self._root=Path(legacy_root) if legacy_root else self._base.parent
        self._old=self._root/'个人工具中心';self._games_path=self._root/'游戏管家/data/library.json'
        self._materials_path=self._old/'data/materials.json';self._wheel_path=self._old/'data/wheel.json'
        self._settings_path=self._base/'data/settings.json';self._lock=threading.RLock();self._opener=opener or os.startfile
        self._jobs={};self._pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='tool-center-pack')
        self._allowed_files=set();self._allowed_outputs={str((self._base/'打包文件').resolve())};self._window=None
        self._icons=SteamIcons()
        self._manager=old_center.ToolManager(self._old,self._tool_specs(),windows=IntegratedWindows(self._root))
        self._actions={name:getattr(self,'_'+name) for name in (
            'bootstrap','launch_tool','game_list','game_favorite','game_save','game_add','game_add_tool','game_open',
            'materials_choose','materials_open','pick_files','pick_output','pack_previous','pack_start','pack_materials',
            'job_status','job_open','wheel_get','wheel_save','wheel_add','wheel_import','wheel_draw','steam_open','settings_save','open_folder')}

    def call(self,action,payload=None):
        try:
            if not isinstance(action,str) or action not in self._actions:raise ValueError('不支持的操作')
            if payload is None:payload={}
            if not isinstance(payload,dict) or len(json.dumps(payload,ensure_ascii=False))>2*1024*1024:raise ValueError('操作参数无效或过大')
            return {'ok':True,'data':self._actions[action](payload)}
        except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
            logging.getLogger('toolcenter').info('%s: %s',action,exc)
            return {'ok':False,'error':str(exc) or '操作未完成，请检查文件是否仍在原位置'}
        except Exception:
            logging.getLogger('toolcenter').exception('Bridge action failed: %s',action)
            return {'ok':False,'error':'操作暂未完成，请打开日志查看原因。'}

    def _tool_specs(self):
        Tool=old_center.Tool
        result=[Tool('town','小镇与专注','布置家园、陪伴伙伴，在同一座小镇里安静专注。',self._root/'宝可梦小镇新版/app.py','宝可梦小镇与专注','#66845d','镇') if item.id=='town' else item for item in old_center.tools_for(self._old)]
        result.extend((Tool('legacy','旧版工具中心','需要时回到原来的界面',self._old/'app.py','个人工具中心','#63798e','旧'),
            Tool('icons','图标换装台','预览宝可梦图标与还原桌面',self._base/'icons.py','桌面宝可梦换装台','#6c56a5','图')))
        return result

    def _state(self):return store.load(self._settings_path)
    def _update_state(self,**changes):
        with self._lock:
            state=self._state();state.update(changes);store.save(self._settings_path,state);return state
    def _record(self,key,name):
        try:
            with self._lock:
                state=self._state();recent=[r for r in state['recent'] if r['id']!=key]
                recent.insert(0,dict(id=key,name=name,time=datetime.now().isoformat(timespec='seconds')))
                state['recent']=recent[:30];store.save(self._settings_path,state)
        except (OSError,ValueError):logging.getLogger('toolcenter').warning('Recent record not saved')
    def _file(self,path):
        p=Path(path);exists=p.is_file()
        return dict(path=str(p),name=p.name,size=p.stat().st_size if exists else 0,exists=exists)
    def _games(self):return game_library.load_library(self._games_path)
    def _game(self,key):
        game=next((g for g in self._games() if g.id==key),None)
        if game is None:raise ValueError('游戏条目不存在，请刷新列表')
        return game
    def _serialize_game(self,game):
        value=asdict(game);value['tools']=[dict(name=Path(p).name,path=p,exists=Path(p).is_file()) for p in game.tool_paths]
        value['tool_count']=len(game.tool_paths);value['icon']=self._icons.get(game.steam_appid);return value
    def _game_list(self,p):return {'games':[self._serialize_game(g) for g in trainers.ordered_games(self._games())]}
    def _material_values(self):
        config=materials.load(self._materials_path);result={}
        for key,title in MATERIAL_NAMES.items():
            path=Path(config[key]) if config[key] else None
            exists=bool(path and (path.is_dir() if key=='charts' else path.is_file()))
            result[key]=dict(id=key,title=title,path=config[key],name=path.name if path else '',exists=exists,is_dir=key=='charts',modified=datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M') if exists else '')
            if exists and key!='charts':self._allowed_files.add(str(path.resolve()))
        return result
    def _bootstrap(self,p):
        warnings=[]
        def safe(fn,default):
            try:return fn()
            except (OSError,ValueError,TypeError) as exc:warnings.append(str(exc));return deepcopy(default)
        state=safe(self._state,store.DEFAULT);games=safe(lambda:self._game_list({})['games'],[])
        material=safe(self._material_values,{k:dict(id=k,title=t,path='',name='',exists=False,is_dir=k=='charts',modified='') for k,t in MATERIAL_NAMES.items()})
        wheel=safe(self._wheel_value,wheel_model.default_wheel());statuses=self._manager.poll();tools=[]
        categories={'games':'game','delivery':'work','town':'fun','status':'system','legacy':'system','focus':'fun','icons':'system'}
        for spec in self._tool_specs():
            status=statuses.get(spec.id,{});state_name=status.get('state','idle')
            tools.append(dict(id=spec.id,name=spec.name,description=spec.description,category=categories[spec.id],status='idle' if state_name=='exited' else state_name,message=status.get('message','尚未打开')))
        files=[self._file(path) for path in state['pack_files']];self._allowed_files.update(str(Path(f['path']).resolve()) for f in files if f['exists'])
        output=state['output_dir'] or str((self._base/'打包文件').resolve());self._allowed_outputs.add(str(Path(output).resolve()))
        with self._lock:jobs=deepcopy(list(self._jobs.values()))
        return dict(app=dict(name='个人工具中心',version='2.0.0',platform='Windows'),settings={k:state[k] for k in ('theme','font_scale')},tools=tools,games=games,materials=material,wheel=wheel,jobs=jobs,recent=state['recent'],pack=dict(files=files,output_dir=output),warnings=warnings)

    def _launch_tool(self,p):
        key=p.get('id');spec=next((s for s in self._tool_specs() if s.id==key),None)
        if spec is None:raise ValueError('未知工具入口')
        with self._lock:result=self._manager.open(key)
        self._record(key,spec.name);return result
    def _game_favorite(self,p):
        if type(p.get('favorite')) is not bool:raise ValueError('收藏状态无效')
        with self._lock:
            games=self._games();game=next((g for g in games if g.id==p.get('id')),None)
            if game is None:raise ValueError('游戏不存在')
            game.favorite=p['favorite'];game_library.save_library(self._games_path,games)
        return self._game_list({})
    def _game_save(self,p):
        name=p.get('name');english=p.get('english_name','');aliases=p.get('aliases',[]);notes=p.get('notes','')
        if not isinstance(name,str) or not name.strip() or len(name)>200 or not isinstance(english,str) or len(english)>200:raise ValueError('请输入200字以内的游戏名称')
        if not isinstance(notes,str) or len(notes)>5000 or not isinstance(aliases,list) or len(aliases)>30 or any(not isinstance(x,str) or len(x)>200 for x in aliases):raise ValueError('别名或备注格式无效')
        with self._lock:
            games=self._games();game=next((g for g in games if g.id==p.get('id')),None)
            if game is None:raise ValueError('游戏不存在')
            game.name=name.strip();game.english_name=english.strip();game.aliases=aliases;game.notes=notes
            game_library.save_library(self._games_path,games)
        return self._game_list({})
    def _game_add(self,p):
        name=p.get('name','');english=p.get('english_name','');appid=p.get('steam_appid','')
        if not isinstance(name,str) or not name.strip() or len(name)>200 or not isinstance(english,str) or len(english)>200:raise ValueError('请输入游戏名称')
        if not isinstance(appid,str) or (appid and not re.fullmatch(r'[0-9]{1,12}',appid)):raise ValueError('Steam AppID必须是数字')
        with self._lock:
            games=self._games();games.append(game_library.Game(uuid.uuid4().hex,name.strip(),english_name=english.strip(),steam_appid=appid));game_library.save_library(self._games_path,games)
        return self._game_list({})
    def _picker(self,folder=False,multiple=False,file_types=()):
        if self._window is None:raise ValueError('文件选择器尚未就绪，请等待窗口加载')
        return self._window.create_file_dialog(20 if folder else 10,allow_multiple=multiple,file_types=file_types)
    def _game_add_tool(self,p):
        self._game(p.get('id'));chosen=self._picker(file_types=('修改器 (*.exe)',))
        if not chosen:return dict(cancelled=True,**self._game_list({}))
        path=Path(chosen[0]).resolve()
        if path.suffix.lower()!='.exe' or not path.is_file() or trainers.excluded(path):raise ValueError('请选择普通修改器EXE；WeMod和Cheat Engine不在此入口管理')
        with self._lock:
            games=self._games();game=next(g for g in games if g.id==p['id'])
            if str(path).casefold() not in {v.casefold() for v in game.tool_paths}:game.tool_paths.append(str(path))
            if not game.preferred_tool:game.preferred_tool=str(path)
            game_library.save_library(self._games_path,games)
        return dict(cancelled=False,**self._game_list({}))
    def _game_open(self,p):
        game=self._game(p.get('id'));kind=p.get('kind')
        if kind=='steam':return self._steam_open({'appid':game.steam_appid})
        if kind=='tool':
            index=p.get('tool_index',0)
            if type(index) is not int or not 0<=index<len(game.tool_paths):raise ValueError('还没有可用修改器，请先添加')
            target=Path(game.tool_paths[index])
            if trainers.excluded(target):raise ValueError('此入口不启动WeMod或Cheat Engine')
            if not target.is_file() or target.suffix.lower()!='.exe':raise ValueError('修改器文件已移动或不是可执行文件，请重新添加')
        elif kind=='folder':
            values=[game.steam_install,game.save_dir]+[str(Path(v).parent) for v in game.tool_paths]
            target=next((Path(v) for v in values if v and Path(v).is_dir()),None)
            if target is None:raise ValueError('还没有可打开的安装或修改器文件夹')
        else:raise ValueError('不支持的游戏操作')
        if not target.exists():raise ValueError('文件已移动或不存在，请重新添加')
        self._opener(str(target.resolve()));self._mark_game_used(game.id);return {'message':'已打开 '+target.name}
    def _mark_game_used(self,key):
        with self._lock:
            games=self._games();game=next((g for g in games if g.id==key),None)
            if game is None:return
            game.last_used=datetime.now().isoformat(timespec='seconds');game_library.save_library(self._games_path,games)
        self._record('game:'+game.id,game.name)
    def _steam_open(self,p):
        appid=p.get('appid')
        if not isinstance(appid,str) or not re.fullmatch(r'[0-9]{1,12}',appid):raise ValueError('该游戏尚未关联有效的Steam AppID')
        known={g.steam_appid for g in self._games()}
        try:known.update(x['appid'] for x in self._wheel_value()['entries'])
        except (ValueError,OSError):pass
        if appid not in known:raise ValueError('游戏不在当前资料库或转盘候选中')
        self._opener('steam://rungameid/'+appid)
        game=next((g for g in self._games() if g.steam_appid==appid),None)
        if game:self._mark_game_used(game.id)
        else:
            try:entry=next(x for x in self._wheel_value()['entries'] if x['appid']==appid);self._record('steam:'+appid,entry['name'])
            except (StopIteration,OSError,ValueError):pass
        return {'message':'已请求Steam启动游戏'}

    def _materials_choose(self,p):
        key=p.get('id')
        if key not in MATERIAL_NAMES:raise ValueError('未知资料类型')
        config=materials.load(self._materials_path);chosen=self._picker(folder=key=='charts')
        if not chosen:return dict(cancelled=True,materials=self._material_values())
        path=Path(chosen[0]).resolve()
        if not (path.is_dir() if key=='charts' else path.is_file()):raise ValueError('所选资料不存在')
        config[key]=str(path);materials.save(self._materials_path,config);return dict(cancelled=False,materials=self._material_values())
    def _materials_open(self,p):
        key=p.get('id')
        if key not in MATERIAL_NAMES:raise ValueError('未知资料类型')
        value=self._material_values()[key]
        if not value['exists']:raise ValueError('请先选择存在的资料文件')
        self._opener(value['path']);return {'message':'已打开 '+value['name']}
    def _pick_files(self,p):
        chosen=self._picker(multiple=True)
        if not chosen:return {'cancelled':True,'files':[]}
        paths=[]
        for value in chosen:
            path=Path(value).resolve()
            if not path.is_file():raise ValueError('所选文件不存在')
            self._allowed_files.add(str(path));paths.append(self._file(str(path)))
        if len(paths)>500:raise ValueError('一次最多选择500个文件')
        return {'cancelled':False,'files':paths}
    def _pick_output(self,p):
        chosen=self._picker(folder=True)
        if not chosen:return {'cancelled':True,'path':''}
        path=Path(chosen[0]).resolve()
        if not path.is_dir():raise ValueError('输出目录不存在')
        self._allowed_outputs.add(str(path));self._update_state(output_dir=str(path));return {'cancelled':False,'path':str(path)}
    def _pack_previous(self,p):
        state=self._state();files=[self._file(v) for v in state['pack_files']]
        self._allowed_files.update(str(Path(v['path']).resolve()) for v in files if v['exists'])
        output=state['output_dir'] or str((self._base/'打包文件').resolve());self._allowed_outputs.add(str(Path(output).resolve()))
        return dict(files=files,output_dir=output)
    def _pack_start(self,p):
        paths=p.get('files');state=self._state()
        if not isinstance(paths,list) or not paths or len(paths)>500 or any(not isinstance(v,str) for v in paths):raise ValueError('请先选择1至500个文件')
        paths=list(dict.fromkeys(str(Path(v).resolve()) for v in paths))
        if any(v not in self._allowed_files for v in paths):raise ValueError('请通过文件选择器或已保存的资料入口选择文件')
        output=p.get('output_dir') or state['output_dir'] or str((self._base/'打包文件').resolve())
        if not isinstance(output,str) or str(Path(output).resolve()) not in self._allowed_outputs:raise ValueError('请先用目录选择器选择输出位置')
        output=str(Path(output).resolve())
        with self._lock:
            if self._busy():raise ValueError('已有打包任务，请完成后再开始')
            self._update_state(pack_files=paths,output_dir=output)
            key=uuid.uuid4().hex;job=dict(id=key,status='queued',message='等待开始',progress=0,result_path='',error='');self._jobs[key]=job
            self._pool.submit(self._pack_worker,key,paths,output)
            return {'job':deepcopy(job)}
    def _pack_worker(self,key,paths,output):
        def progress(message):
            match=re.search(r'(\d+)/(\d+)',message)
            with self._lock:self._jobs[key].update(status='running',message=message,progress=min(95,round(90*int(match[1])/int(match[2]))) if match else 5)
        try:
            result=quickpack.create_zip(paths,output,progress)
            with self._lock:self._jobs[key].update(status='completed',message='压缩包已生成并校验',progress=100,result_path=str(result))
            self._record('pack','文件打包')
        except Exception as exc:
            with self._lock:self._jobs[key].update(status='failed',message='打包未完成',error=str(exc),progress=0)
            logging.getLogger('toolcenter').exception('Pack failed')
    def _pack_materials(self,p):
        self._material_values();paths=materials.pack_files(materials.load(self._materials_path));return self._pack_start(dict(files=[str(v) for v in paths],output_dir=p.get('output_dir')))
    def _busy(self):
        with self._lock:return any(job['status'] in ('queued','running') for job in self._jobs.values())
    def _job_status(self,p):
        with self._lock:
            if p.get('id') not in self._jobs:raise ValueError('任务不存在，请刷新')
            return {'job':deepcopy(self._jobs[p['id']])}
    def _job_open(self,p):
        job=self._job_status(p)['job']
        if job['status']!='completed' or not Path(job['result_path']).is_file():raise ValueError('压缩包尚未生成或已移动')
        self._opener(str(Path(job['result_path']).parent));return {'message':'已打开压缩包所在目录'}

    def _wheel_value(self):return playful_store.load_json(self._wheel_path,wheel_model.default_wheel(),wheel_model.validate_wheel)
    def _wheel_persist(self,value):playful_store.save_json(self._wheel_path,value,wheel_model.default_wheel(),wheel_model.validate_wheel)
    def _wheel_get(self,p):return {'wheel':self._wheel_value()}
    def _wheel_save(self,p):
        draft=p.get('wheel')
        if not isinstance(draft,dict):raise ValueError('转盘设置无效')
        with self._lock:
            old=self._wheel_value();value=dict(old,entries=draft.get('entries',old['entries']),exclude_recent=draft.get('exclude_recent',old['exclude_recent']),challenge=draft.get('challenge',old['challenge']))
            self._wheel_persist(value)
        return {'wheel':value}
    def _wheel_add(self,p):
        name=p.get('name','')
        if not isinstance(name,str) or not name.strip() or len(name)>200:raise ValueError('请输入200字以内的候选名称')
        with self._lock:
            value=self._wheel_value();value['entries'].append(dict(id='custom-'+uuid.uuid4().hex,name=name.strip(),appid='',enabled=True));self._wheel_persist(value)
        return {'wheel':value}
    def _wheel_import(self,p):
        with self._lock:
            value=self._wheel_value();before=len(value['entries']);entries,warnings=wheel_steam.import_installed(self._old,value['entries']);value['entries']=entries;self._wheel_persist(value)
        return {'wheel':value,'added':len(entries)-before,'warnings':warnings}
    def _wheel_draw(self,p):
        import random
        with self._lock:
            value=self._wheel_value();entry=wheel_model.draw(value['entries'],value['recent'],value['exclude_recent'])
            value['recent']=(value['recent']+[entry['id']])[-3:];self._wheel_persist(value)
        result=dict(entry,icon=self._icons.get(entry.get('appid','')))
        return dict(entry=result,recent=value['recent'],challenge=random.choice(CHALLENGES) if value['challenge'] else '')
    def _settings_save(self,p):
        state=self._update_state(theme=p.get('theme'),font_scale=p.get('font_scale'));return {'settings':{k:state[k] for k in ('theme','font_scale')}}
    def _open_folder(self,p):
        values={'data':self._base/'data','logs':self._base/'logs','output':Path(self._state()['output_dir'] or self._base/'打包文件')}
        if p.get('kind') not in values:raise ValueError('未知目录类型')
        folder=values[p['kind']];folder.mkdir(parents=True,exist_ok=True);self._opener(str(folder.resolve()));return {'message':'已打开目录'}
    def _shutdown(self):self._pool.shutdown(wait=True)
