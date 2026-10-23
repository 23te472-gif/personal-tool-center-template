import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Check,
  Dices,
  Gamepad2,
  Play,
  Plus,
  RotateCw,
  Sparkles,
  Star,
  TriangleAlert,
  X,
} from 'lucide-react';
import { isNumericAppId } from '../lib/format.js';
import { getSafeGameIcon } from '../lib/gameIcon.js';
import { useToast } from '../components/Toasts.jsx';
import {
  Badge,
  Button,
  EmptyState,
  InlineAlert,
  PageHeader,
  SectionHeader,
  Spinner,
  Switch,
} from '../components/ui.jsx';

const WHEEL_COLORS = [
  '#6f8fa3',
  '#54a58e',
  '#d3a15f',
  '#8a7fb5',
  '#c47c7c',
  '#5f9cb8',
  '#7fa86a',
  '#b08a62',
  '#917fa3',
  '#68a6a0',
];

function serializeWheel(wheel) {
  return {
    entries: (wheel.entries || []).map((entry) => ({
      ...entry,
      enabled: Boolean(entry.enabled),
    })),
    exclude_recent: Boolean(wheel.exclude_recent),
    challenge: wheel.challenge,
  };
}

function wheelGradient(entries) {
  if (!entries.length) return null;
  const step = 360 / entries.length;
  const colors = entries
    .map((entry, index) => {
      const color = WHEEL_COLORS[index % WHEEL_COLORS.length];
      return `${color} ${index * step}deg ${(index + 1) * step}deg`;
    })
    .join(', ');
  const ticks = `repeating-conic-gradient(from -90deg, rgba(255,255,255,0.28) 0deg 1.2deg, transparent 1.2deg ${step}deg)`;
  return `${ticks}, conic-gradient(from -90deg, ${colors})`;
}

function ResultIcon({ icon }) {
  const [failed, setFailed] = useState(false);
  const source = getSafeGameIcon({ icon });
  return (
    <span className="result-card__icon" aria-hidden="true">
      {source && !failed ? (
        <img src={source} alt="" width="80" height="80" onError={() => setFailed(true)} />
      ) : <Gamepad2 size={36} />}
    </span>
  );
}

export function WheelPage({ data, call, updateWheel, focusWheelId, onFocusConsumed }) {
  const toast = useToast();
  const initialWheel = data.wheel || { entries: [], recent: [], exclude_recent: false, challenge: null };
  const [wheel, setWheel] = useState(initialWheel);
  const [newName, setNewName] = useState('');
  const [pending, setPending] = useState(null);
  const [saveState, setSaveState] = useState('saved');
  const [saveError, setSaveError] = useState(null);
  const [pageError, setPageError] = useState(null);
  const [importWarnings, setImportWarnings] = useState([]);
  const [drawing, setDrawing] = useState(false);
  const [spinning, setSpinning] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [result, setResult] = useState(null);
  const [drawError, setDrawError] = useState(null);
  const [highlightId, setHighlightId] = useState(null);

  const wheelRef = useRef(initialWheel);
  const dirtyRef = useRef(false);
  const saveVersionRef = useRef(0);
  const saveChainRef = useRef(Promise.resolve());
  const spinTimerRef = useRef(null);
  const highlightTimerRef = useRef(null);

  const entries = Array.isArray(wheel.entries) ? wheel.entries : [];
  const enabledEntries = useMemo(() => entries.filter((entry) => entry.enabled), [entries]);
  const recent = Array.isArray(wheel.recent) ? wheel.recent : [];
  const gradient = useMemo(() => wheelGradient(enabledEntries), [enabledEntries]);
  const busy = drawing || spinning || pending !== null;
  const segmentAngle = enabledEntries.length ? 360 / enabledEntries.length : 360;

  useEffect(() => {
    wheelRef.current = wheel;
  }, [wheel]);

  useEffect(() => {
    if (dirtyRef.current || saveState === 'saving') return;
    const incoming = data.wheel;
    if (!incoming || typeof incoming !== 'object') return;
    wheelRef.current = incoming;
    setWheel(incoming);
  }, [data.wheel, saveState]);

  useEffect(() => {
    if (!focusWheelId) return;
    setHighlightId(String(focusWheelId));
    if (highlightTimerRef.current) window.clearTimeout(highlightTimerRef.current);
    highlightTimerRef.current = window.setTimeout(() => setHighlightId(null), 2600);
    const node = document.querySelector(
      `[data-entry-id="${String(focusWheelId).replace(/"/g, '\\"')}"]`
    );
    if (node && typeof node.scrollIntoView === 'function') {
      node.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
    if (onFocusConsumed) onFocusConsumed();
    // 只在外部深链变化时处理。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusWheelId]);

  useEffect(
    () => () => {
      if (spinTimerRef.current) window.clearTimeout(spinTimerRef.current);
      if (highlightTimerRef.current) window.clearTimeout(highlightTimerRef.current);
    },
    []
  );

  function setLocalWheel(next) {
    wheelRef.current = next;
    setWheel(next);
  }

  function enqueueSave(next, { quiet = false } = {}) {
    const version = ++saveVersionRef.current;
    dirtyRef.current = true;
    setSaveState('saving');
    setSaveError(null);

    const run = async () => {
      const response = await call('wheel_save', { wheel: serializeWheel(next) });
      if (version === saveVersionRef.current) {
        if (response.ok) {
          dirtyRef.current = false;
          setSaveState('saved');
          setSaveError(null);
          if (response.data && response.data.wheel) {
            updateWheel(response.data.wheel);
          }
        } else {
          setSaveState('error');
          setSaveError(response.error);
          if (!quiet) {
            toast({ tone: 'error', title: '候选设置未保存', message: response.error });
          }
        }
      }
      return response;
    };

    const queued = saveChainRef.current.then(run, run);
    saveChainRef.current = queued.then(
      () => undefined,
      () => undefined
    );
    return queued;
  }

  function updateAndSave(updater) {
    const next = updater(wheelRef.current);
    setLocalWheel(next);
    enqueueSave(next);
    return next;
  }

  function handleToggleEntry(entry) {
    if (spinning || drawing) return;
    updateAndSave((current) => ({
      ...current,
      entries: current.entries.map((item) =>
        String(item.id) === String(entry.id)
          ? { ...item, enabled: !item.enabled }
          : item
      ),
    }));
  }

  function handleExcludeRecent(value) {
    updateAndSave((current) => ({ ...current, exclude_recent: value }));
  }

  async function handleAddEntry(event) {
    event.preventDefault();
    const name = newName.trim();
    if (!name) return;
    setPending('add');
    setPageError(null);
    const response = await call('wheel_add', { name });
    setPending(null);
    if (!response.ok) {
      setPageError(response.error);
      return;
    }
    const next = response.data && response.data.wheel;
    if (next) {
      setLocalWheel(next);
      dirtyRef.current = false;
      setSaveState('saved');
      updateWheel(next);
    }
    setNewName('');
    toast({ tone: 'success', title: '候选已添加', message: `${name} 已写入本地转盘配置。` });
  }

  async function handleImport() {
    setPending('import');
    setPageError(null);
    setImportWarnings([]);
    const response = await call('wheel_import', {});
    setPending(null);
    if (!response.ok) {
      setPageError(response.error);
      return;
    }
    const payload = response.data || {};
    if (payload.wheel) {
      setLocalWheel(payload.wheel);
      dirtyRef.current = false;
      setSaveState('saved');
      updateWheel(payload.wheel);
    }
    if (Array.isArray(payload.warnings) && payload.warnings.length) {
      setImportWarnings(payload.warnings);
    }
    const added = Number(payload.added) || 0;
    toast({
      tone: added > 0 ? 'success' : 'info',
      title: added > 0 ? `已导入 ${added} 个 Steam 候选` : '没有新增 Steam 候选',
      message:
        added > 0
          ? '只读取本机已安装游戏列表，不登录 Steam，也不发起网络请求。'
          : '本机 Steam 候选可能已经全部在转盘中。',
    });
  }

  async function retrySave() {
    const response = await enqueueSave(wheelRef.current);
    if (response.ok) {
      toast({ tone: 'success', title: '候选设置已保存', message: '本地配置已同步。' });
    }
  }

  async function handleDraw() {
    if (!enabledEntries.length || busy) return;
    setDrawing(true);
    setDrawError(null);
    setPageError(null);
    setResult(null);

    await saveChainRef.current;
    if (dirtyRef.current) {
      const saved = await enqueueSave(wheelRef.current, { quiet: true });
      if (!saved.ok) {
        setDrawing(false);
        setDrawError(saved.error || '候选设置尚未保存，无法开始抽取。');
        return;
      }
    }

    const response = await call('wheel_draw', {});
    setDrawing(false);
    if (!response.ok) {
      setDrawError(response.error);
      return;
    }
    const payload = response.data || {};
    const entry = payload.entry;
    if (!entry || typeof entry !== 'object') {
      setDrawError('本地服务没有返回有效的抽取结果，请重试。');
      return;
    }

    const nextRecent = Array.isArray(payload.recent) ? payload.recent : recent;
    const nextChallenge =
      payload.challenge === undefined ? wheelRef.current.challenge : payload.challenge;
    const nextWheel = {
      ...wheelRef.current,
      recent: nextRecent,
      challenge: nextChallenge,
    };
    setLocalWheel(nextWheel);
    updateWheel(nextWheel);

    const index = enabledEntries.findIndex((item) => String(item.id) === String(entry.id));
    const landingIndex = index >= 0 ? index : 0;
    const currentRotation = rotation;
    const turns = 4 + (landingIndex % 2);
    const targetCenter = (landingIndex + 0.5) * segmentAngle;
    const targetRotation =
      currentRotation + turns * 360 + ((360 - targetCenter) % 360);
    setRotation(targetRotation);
    setSpinning(true);

    const reducedMotion =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const duration = reducedMotion ? 120 : 1450;
    if (spinTimerRef.current) window.clearTimeout(spinTimerRef.current);
    spinTimerRef.current = window.setTimeout(() => {
      setSpinning(false);
      setResult({
        entry,
        recent: nextRecent,
        challenge: nextChallenge,
      });
    }, duration);
  }

  async function handleLaunchResult() {
    const appid = result && result.entry && result.entry.appid;
    if (!isNumericAppId(appid)) return;
    setPending('steam');
    setDrawError(null);
    const response = await call('steam_open', { appid: String(appid) });
    setPending(null);
    if (!response.ok) {
      setDrawError(response.error);
      toast({ tone: 'error', title: '无法启动 Steam 游戏', message: response.error });
      return;
    }
    toast({
      tone: 'success',
      title: '已请求启动 Steam 游戏',
      message: (response.data && response.data.message) || '启动请求已交给本地服务。',
    });
  }

  const resultEntry = result && result.entry;
  const resultAppId = resultEntry && resultEntry.appid;
  const challengeText =
    result && typeof result.challenge === 'string' && result.challenge.trim()
      ? result.challenge
      : '';

  return (
    <div className="page wheel-page">
      <PageHeader
        eyebrow="游戏转盘"
        title="今天玩点什么？"
        description="勾选候选、添加自定义或导入本机 Steam 游戏。抽取结果由本地服务生成；动画只是展示，不会自动启动游戏。"
        actions={
          <>
            <Button
              variant="secondary"
              icon={RotateCw}
              loading={pending === 'import'}
              disabled={spinning || drawing}
              onClick={handleImport}
            >
              导入 Steam 候选
            </Button>
            <Button
              variant="primary"
              icon={Dices}
              loading={drawing}
              disabled={!enabledEntries.length || spinning || drawing}
              onClick={handleDraw}
              title={enabledEntries.length ? '从已勾选候选中抽取' : '请先勾选至少一个候选'}
            >
              {spinning ? '抽取中…' : '开始抽取'}
            </Button>
          </>
        }
      />

      {pageError ? (
        <InlineAlert tone="error" title="转盘操作遇到问题" onDismiss={() => setPageError(null)}>
          {pageError}
        </InlineAlert>
      ) : null}
      {importWarnings.length ? (
        <InlineAlert tone="warning" title="导入 Steam 候选时的提醒" onDismiss={() => setImportWarnings([])}>
          <ul className="alert-list">
            {importWarnings.map((warning, index) => (
              <li key={`${index}-${String(warning).slice(0, 20)}`}>{warning}</li>
            ))}
          </ul>
        </InlineAlert>
      ) : null}

      <div className="wheel-layout">
        <div className="wheel-main">
          <section className="panel wheel-stage" aria-labelledby="wheel-stage-title">
            <SectionHeader
              id="wheel-stage-title"
              title="候选转盘"
              description={`${enabledEntries.length} / ${entries.length} 个候选已勾选`}
              action={
                <span className={`save-state save-state--${saveState}`}>
                  {saveState === 'saving' ? (
                    <>
                      <Spinner size={13} /> 保存中
                    </>
                  ) : saveState === 'error' ? (
                    <>
                      <TriangleAlert size={13} /> 未保存
                    </>
                  ) : (
                    <>
                      <Check size={13} /> 已保存
                    </>
                  )}
                </span>
              }
            />

            <div className={`wheel-scene ${spinning ? 'is-spinning' : ''}`.trim()}>
              <div className="wheel-pointer" aria-hidden="true" />
              <div
                className="wheel-face"
                style={{
                  backgroundImage: gradient || undefined,
                  transform: `rotate(${rotation}deg)`,
                }}
                aria-hidden="true"
              >
                <div className="wheel-face__lines" />
                <div className="wheel-hub">
                  <Dices size={30} />
                  <strong>{enabledEntries.length}</strong>
                  <span>候选</span>
                </div>
              </div>
            </div>

            {!enabledEntries.length ? (
              <div className="wheel-stage__empty">
                <p>还没有勾选任何候选。可在右侧勾选已有候选，或添加自定义候选。</p>
                <Button
                  size="sm"
                  variant="secondary"
                  icon={RotateCw}
                  loading={pending === 'import'}
                  onClick={handleImport}
                >
                  从 Steam 导入
                </Button>
              </div>
            ) : null}

            <div className="wheel-controls">
              <Button
                size="lg"
                variant="primary"
                icon={spinning ? RotateCw : Sparkles}
                loading={drawing}
                disabled={!enabledEntries.length || spinning || drawing}
                onClick={handleDraw}
              >
                {spinning ? '转盘展示中…' : drawing ? '正在请求结果…' : '开始抽取'}
              </Button>
              <p className="muted small">
                先由本地服务生成结果，再播放转盘动画；不会自动启动游戏。
              </p>
            </div>

            {drawError ? (
              <InlineAlert tone="error" title="抽取未完成">
                {drawError}
              </InlineAlert>
            ) : null}
            {saveError ? (
              <InlineAlert
                tone="warning"
                title="候选改动尚未保存"
                action={
                  <Button size="sm" variant="secondary" onClick={retrySave} loading={saveState === 'saving'}>
                    重试保存
                  </Button>
                }
              >
                {saveError}
              </InlineAlert>
            ) : null}

            <div className="recent-wheel">
              <span className="recent-wheel__label">最近结果</span>
              {recent.length ? (
                <div className="recent-wheel__chips">
                  {recent.slice(0, 3).map((name, index) => (
                    <span className="recent-chip" key={`${name}-${index}`}>
                      {name}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="muted small">暂无抽取记录</span>
              )}
            </div>

            <div className="wheel-setting-row">
              <Switch
                id="exclude-recent"
                checked={Boolean(wheel.exclude_recent)}
                onChange={handleExcludeRecent}
                disabled={spinning || drawing}
                label="排除最近三次"
                description="抽取时排除最近三次结果；候选本身仍保留。"
              />
            </div>
          </section>

          <section className="panel wheel-result" aria-live="polite" aria-labelledby="wheel-result-title">
            <SectionHeader id="wheel-result-title" title="抽取结果" description="结果由本地服务生成并保存。" />
            {resultEntry ? (
              <div className="result-card">
                <div className="result-card__glow" aria-hidden="true" />
                <div className="result-card__label">
                  <Sparkles size={15} aria-hidden="true" /> 本次结果
                </div>
                <div className="result-card__identity">
                  <ResultIcon key={`${resultEntry.id}:${resultEntry.icon || ''}`} icon={resultEntry.icon} />
                  <h3>{resultEntry.name || '未命名候选'}</h3>
                </div>
                <div className="result-card__meta">
                  {isNumericAppId(resultAppId) ? (
                    <Badge tone="info">Steam AppID {resultAppId}</Badge>
                  ) : (
                    <Badge tone="neutral">自定义候选</Badge>
                  )}
                  {resultEntry.enabled === false ? <Badge tone="warning">候选当前未勾选</Badge> : null}
                </div>
                {challengeText ? (
                  <div className="result-challenge">
                    <span>挑战</span>
                    <p>{challengeText}</p>
                  </div>
                ) : null}
                <div className="result-card__actions">
                  <Button
                    variant="primary"
                    icon={Play}
                    disabled={!isNumericAppId(resultAppId) || pending === 'steam'}
                    loading={pending === 'steam'}
                    onClick={handleLaunchResult}
                    title={
                      isNumericAppId(resultAppId)
                        ? '显式启动这个 Steam 游戏'
                        : '该候选没有可用的 Steam AppID'
                    }
                  >
                    启动 Steam 游戏
                  </Button>
                  <Button variant="ghost" icon={RotateCw} disabled={busy} onClick={handleDraw}>
                    再抽一次
                  </Button>
                </div>
                <p className="result-card__note">启动只在点击按钮时发生，抽取本身不会打开游戏。</p>
              </div>
            ) : spinning ? (
              <div className="result-placeholder">
                <Spinner size={24} />
                <strong>转盘正在展示…</strong>
                <p>结果已生成，动画结束后显示。</p>
              </div>
            ) : (
              <div className="result-placeholder">
                <span className="result-placeholder__icon">
                  <Dices size={26} aria-hidden="true" />
                </span>
                <strong>等待抽取</strong>
                <p>点击“开始抽取”，结果会写入本地历史，并由你决定是否启动 Steam 游戏。</p>
              </div>
            )}
          </section>
        </div>

        <aside className="wheel-side">
          <section className="panel candidates-panel" aria-labelledby="wheel-candidates-title">
            <SectionHeader
              id="wheel-candidates-title"
              title="候选列表"
              description="勾选后自动保存；至少保留一个候选才能抽取。"
            />
            <form className="candidate-add" onSubmit={handleAddEntry}>
              <label htmlFor="new-candidate" className="sr-only">
                自定义候选名称
              </label>
              <input
                id="new-candidate"
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                placeholder="添加自定义候选…"
                maxLength={100}
                disabled={spinning || drawing || pending === 'add'}
                autoComplete="off"
              />
              <Button
                type="submit"
                variant="secondary"
                icon={Plus}
                loading={pending === 'add'}
                disabled={!newName.trim() || spinning || drawing}
              >
                添加
              </Button>
            </form>

            {entries.length ? (
              <div className="candidate-list">
                {entries.map((entry, index) => {
                  const isRecent = recent.slice(0, 3).includes(entry.name);
                  const highlighted = highlightId && String(highlightId) === String(entry.id);
                  return (
                    <label
                      key={entry.id}
                      data-entry-id={entry.id}
                      className={`candidate-row ${entry.enabled ? 'is-enabled' : ''} ${highlighted ? 'is-highlighted' : ''}`.trim()}
                    >
                      <input
                        type="checkbox"
                        checked={Boolean(entry.enabled)}
                        onChange={() => handleToggleEntry(entry)}
                        disabled={spinning || drawing}
                      />
                      <span
                        className="candidate-row__dot"
                        style={{ background: WHEEL_COLORS[index % WHEEL_COLORS.length] }}
                        aria-hidden="true"
                      />
                      <span className="candidate-row__body">
                        <strong>{entry.name || '未命名候选'}</strong>
                        <small>
                          {entry.appid ? `Steam ${entry.appid}` : '自定义'}
                          {isRecent ? ' · 最近抽中' : ''}
                        </small>
                      </span>
                      {isRecent ? <Star size={13} className="text-warning" aria-label="最近抽中" /> : null}
                    </label>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                compact
                icon={Dices}
                title="还没有转盘候选"
                description="添加自定义候选，或从本机 Steam 已安装游戏导入。"
              />
            )}

            <div className="candidate-actions">
              <Button
                variant="secondary"
                icon={RotateCw}
                loading={pending === 'import'}
                disabled={spinning || drawing}
                onClick={handleImport}
              >
                导入 Steam 候选
              </Button>
              <span className="muted small">{entries.filter((entry) => entry.enabled).length} 个已勾选</span>
            </div>
          </section>

          <section className="panel privacy-card" aria-labelledby="wheel-privacy-title">
            <div className="privacy-card__icon" aria-hidden="true">
              <Sparkles size={20} />
            </div>
            <h2 id="wheel-privacy-title">抽取规则</h2>
            <ul>
              <li>只从已勾选候选中抽取，结果由本地服务生成并保存。</li>
              <li>“排除最近三次”由本地服务应用，界面不会伪造随机结果。</li>
              <li>Steam 导入只读取本机已安装列表，不登录、不联网。</li>
              <li>抽取不会自动启动游戏。</li>
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
}
