import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowRight,
  Clock,
  Dices,
  Gamepad2,
  Package,
  PackageOpen,
  Play,
  Sparkles,
  Star,
  TriangleAlert,
} from 'lucide-react';
import { MATERIAL_LABELS, TOOL_CATEGORY_LABELS } from '../lib/search.js';
import { formatNumber, formatRecentTime, truncateMiddle } from '../lib/format.js';
import { isActiveJob } from '../lib/jobs.js';
import { useToast } from '../components/Toasts.jsx';
import {
  Button,
  EmptyState,
  InlineAlert,
  SectionHeader,
} from '../components/ui.jsx';
import { GameAvatar, MaterialIcon, ToolIcon, toolTone } from '../components/ToolIcon.jsx';
import { JobProgressBar, JobRow, JobStatusBadge } from '../components/JobCard.jsx';

const MATERIAL_IDS = ['thesis', 'presentation', 'charts'];

function materialIsReady(material) {
  return Boolean(material && material.path && material.exists !== false);
}

export function Overview({
  data,
  jobs,
  jobPollError,
  lastUpdated,
  onNavigate,
  onOpenGame,
  onPackMaterialJob,
  call,
  updateMaterials,
  focusToolId,
  onFocusConsumed,
}) {
  const toast = useToast();
  const [pendingTool, setPendingTool] = useState(null);
  const [pendingMaterial, setPendingMaterial] = useState(null);
  const [packingMaterials, setPackingMaterials] = useState(false);
  const [warningsDismissed, setWarningsDismissed] = useState(false);
  const [highlightedTool, setHighlightedTool] = useState(null);
  const highlightTimerRef = useRef(null);

  const games = data.games || [];
  const favoriteGames = games.filter((game) => game.favorite);
  const favorites = favoriteGames.slice(0, 4);
  const recent = (data.recent || []).slice(0, 5);
  const materials = data.materials || {};
  const activeJobs = jobs.filter(isActiveJob);
  const failedJobs = jobs.filter((job) => job.status === 'failed').slice(-1);
  const warnings = data.warnings || [];
  const readyMaterials = MATERIAL_IDS.filter((id) => materialIsReady(materials[id]));
  const tools = data.tools || [];

  useEffect(() => {
    if (!focusToolId) return undefined;
    setHighlightedTool(focusToolId);
    const node = document.querySelector(
      `[data-tool-id="${String(focusToolId).replace(/"/g, '\\"')}"]`
    );
    if (node && typeof node.scrollIntoView === 'function') {
      node.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
    if (highlightTimerRef.current) window.clearTimeout(highlightTimerRef.current);
    highlightTimerRef.current = window.setTimeout(() => setHighlightedTool(null), 2600);
    if (onFocusConsumed) onFocusConsumed();
    return () => {
      if (highlightTimerRef.current) window.clearTimeout(highlightTimerRef.current);
    };
    // 只在外部深链变化时处理。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusToolId]);

  const updateRecentFromGames = useMemo(() => {
    const byId = new Map(games.map((game) => [String(game.id), game]));
    return recent.map((entry) => ({
      ...entry,
      game: byId.get(String(entry.id)) || null,
    }));
  }, [games, recent]);

  async function handleToolAction(tool) {
    if (tool.id === 'games') {
      onNavigate('games');
      return;
    }
    if (tool.id === 'delivery') {
      onNavigate('pack');
      return;
    }
    setPendingTool(tool.id);
    const result = await call('launch_tool', { id: tool.id });
    setPendingTool(null);
    if (!result.ok) {
      toast({ tone: 'error', title: '无法打开工具', message: result.error });
      return;
    }
    const action = result.data && result.data.action;
    const titles = {
      started: '已请求启动',
      focused: '已切换到已打开的窗口',
      pending: '正在准备打开',
    };
    toast({
      tone: action === 'pending' ? 'info' : 'success',
      title: titles[action] || '本地服务已响应',
      message: (result.data && result.data.message) || '启动请求已交给本地服务。',
    });
  }

  async function handleMaterialOpen(id) {
    setPendingMaterial(id);
    const result = await call('materials_open', { id });
    setPendingMaterial(null);
    if (!result.ok) {
      toast({ tone: 'error', title: '无法打开资料', message: result.error });
      return;
    }
    toast({
      tone: 'success',
      title: '已请求打开资料',
      message: (result.data && result.data.message) || MATERIAL_LABELS[id] || '资料',
    });
  }

  async function handleMaterialChoose(id) {
    setPendingMaterial(id);
    const result = await call('materials_choose', { id });
    setPendingMaterial(null);
    if (!result.ok) {
      toast({ tone: 'error', title: '无法选择资料', message: result.error });
      return;
    }
    if (result.data && result.data.cancelled) return;
    if (result.data && result.data.materials) updateMaterials(result.data.materials);
    toast({ tone: 'success', title: '资料入口已更新', message: MATERIAL_LABELS[id] || '资料' });
  }

  async function handlePackMaterials() {
    setPackingMaterials(true);
    const result = await call('pack_materials', {});
    setPackingMaterials(false);
    if (!result.ok) {
      toast({ tone: 'error', title: '无法开始资料打包', message: result.error });
      return;
    }
    const job = result.data && result.data.job;
    if (job && onPackMaterialJob) onPackMaterialJob(job);
    toast({
      tone: 'success',
      title: '资料打包任务已开始',
      message: '任务在本地执行，可在文件打包页查看进度。',
    });
    onNavigate('pack');
  }

  async function handleOpenJob(job) {
    const result = await call('job_open', { id: job.id });
    if (!result.ok) {
      toast({ tone: 'error', title: '无法打开任务位置', message: result.error });
      return;
    }
    toast({
      tone: 'success',
      title: '已请求打开位置',
      message: (result.data && result.data.message) || '已完成任务的结果目录',
    });
  }

  return (
    <div className="page overview-page">
      {warnings.length && !warningsDismissed ? (
        <InlineAlert
          tone="warning"
          title="启动时提醒"
          onDismiss={() => setWarningsDismissed(true)}
          action={
            <Button size="sm" variant="ghost" onClick={() => onNavigate('settings')}>
              查看设置
            </Button>
          }
        >
          <ul className="alert-list">
            {warnings.map((warning, index) => (
              <li key={`${index}-${String(warning).slice(0, 24)}`}>{warning}</li>
            ))}
          </ul>
        </InlineAlert>
      ) : null}

      <section className="hero-card" aria-labelledby="overview-hero-title">
        <div className="hero-card__content">
          <div className="eyebrow eyebrow--light">
            <Sparkles size={14} aria-hidden="true" /> 本地工作台
          </div>
          <h1 id="overview-hero-title">把常用工具，收进一个清爽的入口</h1>
          <p>
            工具、游戏修改器、论文资料与打包任务都在本机完成。这里展示本机资料，
            不会自动启动任何程序，也不会把文件上传到网络。
          </p>
          <div className="hero-card__actions">
            <Button
              variant="primary"
              icon={Gamepad2}
              onClick={() => onNavigate('games')}
            >
              打开游戏管家
            </Button>
            <Button
              variant="soft"
              icon={Package}
              onClick={() => onNavigate('pack')}
            >
              开始文件打包
            </Button>
            <Button
              variant="ghost"
              className="hero-card__text-button"
              icon={Dices}
              onClick={() => onNavigate('wheel')}
            >
              游戏转盘
            </Button>
          </div>
          <div className="hero-stats">
            <span>
              <strong>{formatNumber(games.length)}</strong> 款游戏
            </span>
            <span>
              <strong>{formatNumber(favoriteGames.length)}</strong> 个收藏
            </span>
            <span>
              <strong>{formatNumber(activeJobs.length)}</strong> 个进行中任务
            </span>
          </div>
        </div>
        <div className="hero-card__art" aria-hidden="true">
          <div className="hero-orbit hero-orbit--one" />
          <div className="hero-orbit hero-orbit--two" />
          <div className="hero-glyph">
            <ToolIcon id="games" size={34} />
          </div>
          <div className="hero-chip hero-chip--one">
            <Package size={15} /> 本地打包
          </div>
          <div className="hero-chip hero-chip--two">
            <Star size={15} /> 收藏与最近
          </div>
        </div>
      </section>

      <section aria-labelledby="overview-tools-title">
        <SectionHeader
          id="overview-tools-title"
          title="工具入口"
          description="常用工具与旧版入口。小镇与专注、换装台和状态卡片都按需启动。"
          action={
            <span className="muted small">
              共 {tools.length} 个工具
            </span>
          }
        />
        {tools.length ? (
          <div className="tool-grid">
            {tools.map((tool) => {
              const isInternal = tool.id === 'games' || tool.id === 'delivery';
              const status = tool.status || 'idle';
              return (
                <article
                  className={`tool-card ${highlightedTool === tool.id ? 'is-highlighted' : ''}`.trim()}
                  key={tool.id}
                  data-tool-id={tool.id}
                >
                  <div className="tool-card__top">
                    <span className={`tool-icon tool-icon--${toolTone(tool.id)}`}>
                      <ToolIcon id={tool.id} />
                    </span>
                    <span className="badge badge--neutral">
                      {TOOL_CATEGORY_LABELS[tool.category] || '本地'}
                    </span>
                  </div>
                  <div className="tool-card__body">
                    <h3>{tool.name || tool.id}</h3>
                    <p>{tool.description || '本地工具'}</p>
                  </div>
                  {status !== 'idle' ? (
                    <div className="tool-card__status">
                      <span className={`status-dot status-dot--${status}`} aria-hidden="true" />
                      <span>{tool.message || (status === 'failed' ? '运行异常' : '运行中')}</span>
                    </div>
                  ) : null}
                  <div className="tool-card__footer">
                    <Button
                      size="sm"
                      variant={isInternal ? 'secondary' : 'soft'}
                      loading={pendingTool === tool.id}
                      onClick={() => handleToolAction(tool)}
                      icon={isInternal ? ArrowRight : Play}
                    >
                      {isInternal ? '打开新版' : '启动'}
                    </Button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <EmptyState
            icon={PackageOpen}
            title="尚未配置工具入口"
            description="暂时没有可显示的工具。请检查本地配置或稍后刷新。"
          />
        )}
      </section>

      <section aria-labelledby="overview-materials-title">
        <SectionHeader
          id="overview-materials-title"
          title="资料快捷入口"
          description="论文与演示文稿可在文件打包页直接打包；图表资料可单独打开。"
          action={
            <Button
              size="sm"
              variant="secondary"
              icon={PackageOpen}
              loading={packingMaterials}
              disabled={!readyMaterials.length}
              onClick={handlePackMaterials}
              title={readyMaterials.length ? '把已配置的论文与 PPT 打成 ZIP' : '请先配置至少一项论文或 PPT'}
            >
              一键打包资料
            </Button>
          }
        />
        <div className="material-grid">
          {MATERIAL_IDS.map((id) => {
            const material = materials[id] || { id };
            const ready = materialIsReady(material);
            return (
              <article className={`material-card ${ready ? '' : 'is-unconfigured'}`.trim()} key={id}>
                <div className={`material-icon material-icon--${id}`}>
                  <MaterialIcon id={id} />
                </div>
                <div className="material-card__body">
                  <div className="material-card__title">
                    <h3>{material.title || MATERIAL_LABELS[id]}</h3>
                    {material.path ? (
                      <span className={`badge badge--${material.exists === false ? 'danger' : 'success'}`}>
                        {material.exists === false ? '路径不可用' : '已配置'}
                      </span>
                    ) : (
                      <span className="badge badge--neutral">未配置</span>
                    )}
                  </div>
                  <p className="material-card__path" title={material.path || ''}>
                    {material.path
                      ? truncateMiddle(material.path, 52)
                      : '尚未选择文件或文件夹'}
                  </p>
                  {material.modified ? (
                    <span className="material-card__meta">更新于 {material.modified}</span>
                  ) : null}
                </div>
                <div className="material-card__actions">
                  <Button
                    size="sm"
                    variant="ghost"
                    loading={pendingMaterial === id}
                    onClick={() => handleMaterialChoose(id)}
                  >
                    {material.path ? '更换' : '选择'}
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    icon={ArrowRight}
                    disabled={!ready || pendingMaterial === id}
                    loading={pendingMaterial === id}
                    onClick={() => handleMaterialOpen(id)}
                    title={ready ? '打开资料' : '资料未配置或路径不可用'}
                  >
                    打开
                  </Button>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <div className="overview-columns">
        <section className="panel" aria-labelledby="overview-favorites-title">
          <SectionHeader
            id="overview-favorites-title"
            title="收藏游戏"
            description="常用游戏与修改器入口"
            action={
              <Button size="sm" variant="ghost" icon={ArrowRight} onClick={() => onNavigate('games')}>
                全部
              </Button>
            }
          />
          {favorites.length ? (
            <div className="compact-list">
              {favorites.map((game) => (
                <button
                  type="button"
                  className="compact-game"
                  key={game.id}
                  onClick={() => onOpenGame(game.id)}
                >
                  <GameAvatar game={game} />
                  <span className="compact-game__text">
                    <strong>{game.name || game.english_name || '未命名游戏'}</strong>
                    <small>{game.english_name || (game.aliases || []).join('、') || '无英文名'}</small>
                  </span>
                  <span className="compact-game__meta">
                    <Star size={14} className="text-warning" aria-hidden="true" />
                    {game.tool_count || (game.tools || []).length} 个修改器
                  </span>
                  <ArrowRight size={16} className="compact-game__arrow" aria-hidden="true" />
                </button>
              ))}
            </div>
          ) : (
            <EmptyState
              compact
              icon={Star}
              title="还没有收藏游戏"
              description="在游戏详情中点亮星标，即可把常用游戏放到这里。"
              action={
                <Button size="sm" variant="secondary" onClick={() => onNavigate('games')}>
                  去收藏
                </Button>
              }
            />
          )}
        </section>

        <section className="panel" aria-labelledby="overview-recent-title">
          <SectionHeader
            id="overview-recent-title"
            title="最近使用"
            description="最近打开过的游戏会出现在这里"
          />
          {updateRecentFromGames.length ? (
            <ol className="recent-list">
              {updateRecentFromGames.map((entry, index) => (
                <li key={`${entry.id}-${index}`}>
                  <button
                    type="button"
                    className="recent-item"
                    onClick={() => onOpenGame(entry.id)}
                  >
                    <span className="recent-item__index">{String(index + 1).padStart(2, '0')}</span>
                    <span className="recent-item__body">
                      <strong>{entry.name || (entry.game && entry.game.name) || '游戏'}</strong>
                      <small>
                        <Clock size={12} aria-hidden="true" /> {formatRecentTime(entry.time) || '时间未知'}
                      </small>
                    </span>
                    <ArrowRight size={15} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState
              compact
              icon={Clock}
              title="暂无最近使用记录"
              description="通过新版启动游戏或修改器后，这里会显示本地最近记录。"
            />
          )}
        </section>
      </div>

      <section className="panel" aria-labelledby="overview-jobs-title">
        <SectionHeader
          id="overview-jobs-title"
          title="打包进度"
          description={
            lastUpdated
              ? `最近更新 ${formatRecentTime(lastUpdated)}。`
              : '打包进行时会自动更新进度。'
          }
          action={
            <Button size="sm" variant="ghost" icon={ArrowRight} onClick={() => onNavigate('pack')}>
              文件打包
            </Button>
          }
        />
        {jobPollError ? (
          <InlineAlert tone="warning" title="任务状态更新遇到问题">
            {jobPollError}
          </InlineAlert>
        ) : null}
        {activeJobs.length ? (
          <div className="job-stack">
            {activeJobs.map((job) => (
              <article className="active-job" key={job.id}>
                <div className="active-job__head">
                  <span className="active-job__title">
                    <Package size={16} aria-hidden="true" /> 打包任务 {String(job.id).slice(0, 12)}
                  </span>
                  <JobStatusBadge status={job.status} />
                </div>
                <JobProgressBar job={job} />
              </article>
            ))}
          </div>
        ) : (
          <div className="task-empty">
            <span className="task-empty__icon">
              <Package size={18} aria-hidden="true" />
            </span>
            <div>
              <strong>当前没有进行中的任务</strong>
              <p>选择文件后可开始本地 ZIP 打包，进度会在这里实时更新。</p>
            </div>
            <Button size="sm" variant="secondary" onClick={() => onNavigate('pack')}>
              去打包
            </Button>
          </div>
        )}

        {failedJobs.length ? (
          <div className="job-stack job-stack--failed">
            <div className="job-stack__label">
              <TriangleAlert size={15} aria-hidden="true" /> 最近失败
            </div>
            {failedJobs.map((job) => (
              <JobRow key={job.id} job={job} onGoPack={() => onNavigate('pack')} onOpen={handleOpenJob} />
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}
