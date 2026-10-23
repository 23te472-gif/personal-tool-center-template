import { useCallback, useEffect, useRef, useState } from 'react';
import {
  House,
  Leaf,
  LoaderCircle,
  RotateCw,
  Settings2,
  Sprout,
  Sun,
  Timer,
  X,
} from 'lucide-react';
import { createBridge } from './lib/bridge.js';
import { millisecondsUntilJapanMidnight } from './lib/lifecycle.js';
import {
  canPlace,
  formatClock,
  isSnapshot,
  placedLocation,
  todayStats,
} from './lib/town.js';
import { FocusView } from './components/FocusView.jsx';
import { TownPanel } from './components/TownPanel.jsx';
import { TownScene } from './components/TownScene.jsx';

const AREA_COPY = {
  home: { title: '家园', line: '把喜欢的日常，安放在屋檐下。' },
  plaza: { title: '广场', line: '喷泉边总有风，也总有一点好心情。' },
  orchard: { title: '果园', line: '树影里藏着甜甜的果子，慢慢走。' },
};

function Brand() {
  return (
    <div className="brand">
      <span className="brand__mark" aria-hidden="true">
        <svg viewBox="0 0 40 40">
          <path d="M20 32c-7-3-11-8-11-15 7 0 11 5 11 15Z" fill="#587b60" />
          <path d="M20 32c6-3 10-8 10-15-6 0-10 5-10 15Z" fill="#88a77d" />
          <path d="M20 33V14" stroke="#4e6d55" strokeWidth="2.4" strokeLinecap="round" />
          <path d="M20 19c-4-1-6-4-6-7 4 0 6 3 6 7Z" fill="#b4c99d" opacity=".9" />
        </svg>
      </span>
      <span className="brand__text">
        <strong>苔丘小镇</strong>
        <small>专注小屋</small>
      </span>
    </div>
  );
}

function ConnectionScreen({ status, error, onRetry }) {
  const loading = status === 'connecting';
  return (
    <main className="connection">
      <div className="connection__glow" aria-hidden="true" />
      <div className="connection__card">
        <Brand />
        <div className={`connection__scene ${loading ? 'is-loading' : ''}`.trim()} aria-hidden="true">
          <span className="connection__hill connection__hill--back" />
          <span className="connection__hill connection__hill--front" />
          <span className="connection__house">
            <span className="connection__roof" />
            <span className="connection__door" />
          </span>
          <span className="connection__tree connection__tree--left" />
          <span className="connection__tree connection__tree--right" />
        </div>
        <h1>{loading ? '正在推开小镇的门…' : '小镇还没有醒'}</h1>
        <p>
          {loading
            ? '正在和本地服务打招呼，请稍等片刻。'
            : error || '还没有连上本地服务。请从工具中心重新打开，或重试连接。'}
        </p>
        {loading ? (
          <span className="connection__loader" role="status">
            <LoaderCircle size={18} aria-hidden="true" /> 连接本地小镇
          </span>
        ) : (
          <button type="button" className="button button--primary" onClick={onRetry}>
            <RotateCw size={16} aria-hidden="true" /> 再试一次
          </button>
        )}
      </div>
    </main>
  );
}

function SettingsPopover({ settings, busy, onSave, onClose }) {
  const theme = settings.theme === 'dark' ? 'dark' : 'light';
  const motion = settings.motion !== false;
  return (
    <div className="settings-popover" role="dialog" aria-label="界面设置">
      <div className="settings-popover__head">
        <strong>让小镇更合眼</strong>
        <button type="button" className="icon-button" onClick={onClose} aria-label="关闭设置">
          <X size={17} />
        </button>
      </div>
      <div className="settings-group">
        <span className="settings-label">光线</span>
        <div className="segmented segmented--small">
          <button
            type="button"
            className={theme === 'light' ? 'is-active' : ''}
            aria-pressed={theme === 'light'}
            disabled={Boolean(busy)}
            onClick={() => onSave({ theme: 'light', motion })}
          >
            <Sun size={15} aria-hidden="true" /> 奶油白
          </button>
          <button
            type="button"
            className={theme === 'dark' ? 'is-active' : ''}
            aria-pressed={theme === 'dark'}
            disabled={Boolean(busy)}
            onClick={() => onSave({ theme: 'dark', motion })}
          >
            <Sprout size={15} aria-hidden="true" /> 夜灯
          </button>
        </div>
      </div>
      <div className="settings-group settings-group--row">
        <div>
          <span className="settings-label">伙伴的小动作</span>
          <p>关闭后场景保持安静，计时不受影响。</p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={motion}
          className={`switch ${motion ? 'is-on' : ''}`.trim()}
          disabled={Boolean(busy)}
          onClick={() => onSave({ theme, motion: !motion })}
        >
          <span />
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const bridgeRef = useRef(null);
  if (!bridgeRef.current) bridgeRef.current = createBridge(window);
  const bridge = bridgeRef.current;
  const snapshotRef = useRef(null);
  const actionLock = useRef(false);
  const actionEpoch = useRef(0);
  const toastTimer = useRef(null);
  const [snapshot, setSnapshot] = useState(null);
  const [connection, setConnection] = useState('connecting');
  const [connectionError, setConnectionError] = useState('');
  const [actionError, setActionError] = useState('');
  const [syncError, setSyncError] = useState('');
  const [busy, setBusy] = useState('');
  const [toast, setToast] = useState(null);
  const [hidden, setHidden] = useState(() => document.hidden);
  const [area, setArea] = useState('home');
  const [panel, setPanel] = useState('partner');
  const [selectedItem, setSelectedItem] = useState(null);
  const [edit, setEdit] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsBusy, setSettingsBusy] = useState(false);
  const [bootNonce, setBootNonce] = useState(0);

  const notify = useCallback((message, tone = 'success') => {
    if (!message) return;
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    setToast({ message, tone });
    toastTimer.current = window.setTimeout(() => setToast(null), 3200);
  }, []);

  const applySnapshot = useCallback((next) => {
    if (!isSnapshot(next)) return false;
    snapshotRef.current = next;
    setSnapshot(next);
    setConnection('ready');
    setConnectionError('');
    return true;
  }, []);

  useEffect(() => {
    let disposed = false;
    let inFlight = false;
    let settled = false;
    let probe = null;
    let slowTimer = null;

    const attempt = async () => {
      if (disposed || inFlight || settled || !bridge.available()) return;
      inFlight = true;
      const result = await bridge.call('bootstrap', {});
      if (disposed) return;
      if (result.ok && applySnapshot(result.data)) {
        settled = true;
        if (slowTimer) window.clearTimeout(slowTimer);
        if (probe) window.clearInterval(probe);
        setConnection('ready');
      } else {
        setConnection('error');
        setConnectionError(result.error || '本地服务没有返回完整的小镇数据，请重试。');
      }
      inFlight = false;
    };

    const ready = () => attempt();
    const retry = () => {
      setConnection('connecting');
      setConnectionError('');
      settled = false;
      attempt();
    };

    window.addEventListener('pywebviewready', ready);
    attempt();
    probe = window.setInterval(attempt, 900);
    slowTimer = window.setTimeout(() => {
      if (!disposed && !snapshotRef.current) {
        setConnection('error');
        setConnectionError('还没有连上本地服务。请从工具中心重新打开，或点“再试一次”。');
      }
    }, 4200);

    return () => {
      disposed = true;
      if (probe) window.clearInterval(probe);
      if (slowTimer) window.clearTimeout(slowTimer);
      window.removeEventListener('pywebviewready', ready);
    };
  }, [applySnapshot, bridge, bootNonce]);

  const retryConnection = useCallback(() => {
    setConnection('connecting');
    setConnectionError('');
    setBootNonce((value) => value + 1);
  }, []);

  useEffect(() => {
    const onVisibility = () => setHidden(document.hidden);
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, []);

  const themeSetting = snapshot && snapshot.settings ? snapshot.settings.theme : 'light';
  const motionSetting = snapshot && snapshot.settings ? snapshot.settings.motion !== false : true;

  useEffect(() => {
    document.documentElement.dataset.theme = themeSetting === 'dark' ? 'dark' : 'light';
    document.documentElement.dataset.motion = motionSetting ? 'on' : 'off';
  }, [themeSetting, motionSetting]);

  useEffect(() => {
    document.documentElement.dataset.hidden = hidden ? 'true' : 'false';
  }, [hidden]);

  useEffect(() => {
    if (!settingsOpen) return undefined;
    const onKey = (event) => {
      if (event.key === 'Escape') setSettingsOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [settingsOpen]);

  useEffect(
    () => () => {
      if (toastTimer.current) window.clearTimeout(toastTimer.current);
    },
    []
  );

  const callAction = useCallback(
    async (action, payload = {}, options = {}) => {
      if (actionLock.current) return { ok: false, error: '正在处理上一步，请稍等。' };
      actionLock.current = true;
      actionEpoch.current += 1;
      setBusy(action);
      setActionError('');
      setSyncError('');
      const result = await bridge.call(action, payload);
      if (result.ok && applySnapshot(result.data)) {
        if (!options.quiet && result.data.message) notify(result.data.message);
        actionLock.current = false;
        setBusy('');
        return result;
      }
      const message = result.error || '这一步没有完成，请稍后再试。';
      setActionError(message);
      notify(message, 'error');
      actionLock.current = false;
      setBusy('');
      return { ok: false, error: message };
    },
    [applySnapshot, bridge, notify]
  );

  const focusRunning = Boolean(snapshot && snapshot.focus.active && snapshot.focus.running);

  // Refresh read-only daily state on a new day and when returning from the background.
  // Idle windows do not poll the native bridge; this schedules one midnight read.
  useEffect(() => {
    let disposed = false;
    let timer;
    const refresh = async () => {
      if (document.hidden || actionLock.current || !snapshotRef.current) return;
      const epoch = actionEpoch.current;
      const result = await bridge.call('focus_state', {});
      if (disposed || actionLock.current || epoch !== actionEpoch.current) return;
      if (result.ok && isSnapshot(result.data)) applySnapshot(result.data);
    };
    const schedule = () => {
      timer = window.setTimeout(async () => {
        await refresh();
        if (!disposed) schedule();
      }, millisecondsUntilJapanMidnight());
    };
    const returned = () => { if (!document.hidden) refresh(); };
    document.addEventListener('visibilitychange', returned);
    schedule();
    return () => {
      disposed = true;
      window.clearTimeout(timer);
      document.removeEventListener('visibilitychange', returned);
    };
  }, [bridge, applySnapshot]);

  useEffect(() => {
    if (!edit || edit.mode !== 'move' || !snapshot) return;
    if (!placedLocation(snapshot.town, edit.itemId)) setEdit(null);
  }, [edit, snapshot]);

  useEffect(() => {
    if (!focusRunning || hidden) return undefined;
    let disposed = false;
    let inFlight = false;

    const tick = async () => {
      if (disposed || inFlight || actionLock.current) return;
      inFlight = true;
      const epoch = actionEpoch.current;
      const result = await bridge.call('focus_state', {});
      inFlight = false;
      if (disposed || actionLock.current || epoch !== actionEpoch.current) return;
      if (result.ok && isSnapshot(result.data)) {
        const previousRunning = snapshotRef.current && snapshotRef.current.focus.running;
        const completed = previousRunning && !result.data.focus.running;
        applySnapshot(result.data);
        setSyncError('');
        if (completed && result.data.message) notify(result.data.message);
      } else {
        setSyncError(result.error || '计时同步暂时中断，正在重试。');
      }
    };

    tick();
    const timer = window.setInterval(tick, 1000);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, [focusRunning, hidden, bridge, applySnapshot, notify]);

  const mode = snapshot ? snapshot.settings.mode : 'town';
  const motion = snapshot ? snapshot.settings.motion !== false : true;
  const town = snapshot && snapshot.town;
  const catalog = snapshot && snapshot.catalog;
  const today = snapshot && snapshot.today;
  const focus = snapshot && snapshot.focus;
  const stats = snapshot ? todayStats(town, today) : { sessions: 0, minutes: 0 };
  const currentArea = area;

  function switchMode(next) {
    if (!snapshot || busy || next === mode) return;
    callAction('set_mode', { mode: next }, { quiet: true });
  }

  function changeArea(next) {
    if (!snapshot) return;
    if (!town.areas.includes(next)) {
      setPanel('tasks');
      notify('果园还在小路尽头，先在任务页解锁它。', 'info');
      return;
    }
    setEdit(null);
    setArea(next);
  }

  function startPlace(itemId) {
    setSelectedItem(itemId);
    setEdit({ mode: 'place', itemId });
    setActionError('');
  }

  function startMove(itemId) {
    const location = placedLocation(town, itemId);
    if (!location) return;
    setSelectedItem(itemId);
    setArea(location.area);
    setEdit({ mode: 'move', itemId });
    setActionError('');
  }

  async function placeAt(cell) {
    if (!edit || !snapshot || busy) return;
    const check = canPlace({
      town,
      catalog,
      area,
      itemId: edit.itemId,
      x: cell.x,
      y: cell.y,
      ignoreItemId: edit.itemId,
    });
    if (!check.ok) {
      setActionError(check.reason);
      return;
    }
    const result = await callAction(
      'town_action',
      {
        action: edit.mode,
        args: { item_id: edit.itemId, area, x: cell.x, y: cell.y },
      },
      { quiet: true }
    );
    if (result.ok) {
      setEdit(null);
      notify(edit.mode === 'move' ? '家具挪好了。' : '家具摆好啦。');
    }
  }

  function saveSettings(patch) {
    if (settingsBusy) return;
    setSettingsBusy(true);
    callAction('settings_save', patch, { quiet: true }).finally(() => setSettingsBusy(false));
  }

  if (!snapshot) {
    return (
      <ConnectionScreen
        status={connection}
        error={connectionError}
        onRetry={retryConnection}
      />
    );
  }

  const areaCopy = AREA_COPY[currentArea];
  const activeFocus = focus.active;

  return (
    <div className="app-shell">
      <header className="topbar">
        <Brand />
        <nav className="mode-switch" aria-label="小镇与专注模式">
          <button
            type="button"
            className={mode === 'town' ? 'is-active' : ''}
            aria-pressed={mode === 'town'}
            disabled={Boolean(busy)}
            onClick={() => switchMode('town')}
          >
            <House size={16} aria-hidden="true" />
            小镇
          </button>
          <button
            type="button"
            className={mode === 'focus' ? 'is-active' : ''}
            aria-pressed={mode === 'focus'}
            disabled={Boolean(busy)}
            onClick={() => switchMode('focus')}
          >
            <Timer size={16} aria-hidden="true" />
            专注
          </button>
        </nav>
        <div className="topbar__right">
          {activeFocus && mode === 'town' && (
            <button
              type="button"
              className={`focus-pill ${focus.running ? 'is-running' : ''}`.trim()}
              onClick={() => switchMode('focus')}
              aria-label={`${focus.running ? '专注进行中' : '专注已暂停'}，剩余 ${formatClock(focus.remaining)}，回到专注模式`}
            >
              <span className="focus-pill__dot" aria-hidden="true" />
              <Timer size={15} aria-hidden="true" />
              <span>{formatClock(focus.remaining)}</span>
              <small>{focus.running ? '专注中' : '已暂停'}</small>
            </button>
          )}
          <div className="berry-balance" aria-label={`树果余额 ${town.berries}`}>
            <Leaf size={16} aria-hidden="true" />
            <span>{town.berries}</span>
            <small>树果</small>
          </div>
          <div className="settings-wrap">
            <button
              type="button"
              className={`icon-button ${settingsOpen ? 'is-active' : ''}`.trim()}
              aria-label="界面设置"
              aria-expanded={settingsOpen}
              onClick={() => setSettingsOpen((value) => !value)}
            >
              <Settings2 size={18} aria-hidden="true" />
            </button>
            {settingsOpen && (
              <SettingsPopover
                settings={snapshot.settings}
                busy={settingsBusy || Boolean(busy)}
                onSave={saveSettings}
                onClose={() => setSettingsOpen(false)}
              />
            )}
          </div>
        </div>
      </header>

      <div className="app-body">
        {actionError && (
          <div className="notice notice--error" role="alert">
            <span>{actionError}</span>
            <button type="button" className="notice__close" onClick={() => setActionError('')} aria-label="关闭错误提示">
              <X size={15} />
            </button>
          </div>
        )}
        {syncError && !actionError && (
          <div className="notice notice--warning" role="status">
            <span>{syncError}</span>
            <button type="button" className="notice__close" onClick={() => setSyncError('')} aria-label="关闭同步提示">
              <X size={15} />
            </button>
          </div>
        )}

        {mode === 'town' ? (
          <main className="town-layout">
            <section className="town-stage" aria-labelledby="town-heading">
              <div className="town-stage__head">
                <div>
                  <span className="eyebrow">
                    <Sprout size={14} aria-hidden="true" /> 薄荷色的日常
                  </span>
                  <h1 id="town-heading">{areaCopy.title}</h1>
                  <p>{areaCopy.line}</p>
                </div>
                <div className="area-tabs" role="tablist" aria-label="小镇区域">
                  {catalog.areas.map((item) => {
                    const unlocked = town.areas.includes(item.id);
                    const active = currentArea === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        role="tab"
                        aria-selected={active}
                        className={`area-tab ${active ? 'is-active' : ''} ${!unlocked ? 'is-locked' : ''}`.trim()}
                        onClick={() => changeArea(item.id)}
                      >
                        {item.name}
                        {!unlocked && <small>{item.unlock_cost} 果</small>}
                      </button>
                    );
                  })}
                </div>
              </div>

              {currentArea === 'orchard' && !town.areas.includes('orchard') ? (
                <div className="locked-orchard">
                  <Leaf size={28} aria-hidden="true" />
                  <h2>果园还在小路尽头</h2>
                  <p>用 12 枚树果把木门打开，每天都能来采一次果。</p>
                  <button
                    type="button"
                    className="button button--primary"
                    disabled={Boolean(busy) || town.berries < 12}
                    onClick={() =>
                      callAction('town_action', { action: 'unlock', args: { area: 'orchard' } })
                    }
                  >
                    解锁果园
                  </button>
                </div>
              ) : (
                <TownScene
                  snapshot={snapshot}
                  area={currentArea}
                  motion={motion}
                  hidden={hidden}
                  edit={edit}
                  selectedItem={selectedItem}
                  onCellClick={placeAt}
                  onSelectPlaced={(itemId) => {
                    setSelectedItem(itemId);
                    setPanel('furniture');
                    setEdit(null);
                  }}
                  onCancelEdit={() => setEdit(null)}
                />
              )}

              <div className="town-stage__foot">
                <div className="today-line">
                  <span className="today-line__mark" aria-hidden="true">
                    <Sun size={15} />
                  </span>
                  <span>
                    今天专注 <strong>{stats.minutes}</strong> 分钟 · {stats.sessions} 次
                  </span>
                </div>
                <button
                  type="button"
                  className="text-button"
                  onClick={() => setPanel('stats')}
                >
                  看看这一周
                </button>
              </div>
            </section>

            <TownPanel
              snapshot={snapshot}
              area={currentArea}
              panel={panel}
              onPanelChange={setPanel}
              selectedItem={selectedItem}
              onSelectItem={setSelectedItem}
              onAction={callAction}
              onStartPlace={startPlace}
              onStartMove={startMove}
              onCancelEdit={() => setEdit(null)}
              edit={edit}
              busy={Boolean(busy)}
            />
          </main>
        ) : (
          <main className="focus-page">
            <FocusView
              snapshot={snapshot}
              busy={Boolean(busy)}
              motion={motion}
              hidden={hidden}
              onAction={callAction}
            />
          </main>
        )}
      </div>

      {toast && (
        <div className={`toast toast--${toast.tone}`.trim()} role="status" aria-live="polite">
          <span className="toast__dot" aria-hidden="true" />
          {toast.message}
        </div>
      )}
    </div>
  );
}
