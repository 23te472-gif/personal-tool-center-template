import { useState } from 'react';
import {
  Archive,
  Check,
  FileText,
  FolderOpen,
  Info,
  Monitor,
  Moon,
  RefreshCw,
  Server,
  Settings2,
  Sun,
  TriangleAlert,
} from 'lucide-react';
import { formatDateTime, formatRecentTime } from '../lib/format.js';
import { useToast } from '../components/Toasts.jsx';
import {
  Badge,
  Button,
  InlineAlert,
  PageHeader,
  SectionHeader,
  Spinner,
} from '../components/ui.jsx';

const THEME_OPTIONS = [
  { id: 'light', label: '浅色', description: '清爽明亮，适合白天', icon: Sun },
  { id: 'dark', label: '深色', description: '低亮度，适合夜间', icon: Moon },
];

const FONT_OPTIONS = [
  { value: 0.9, label: '小', sample: '紧凑' },
  { value: 1, label: '标准', sample: '舒适' },
  { value: 1.15, label: '大', sample: '宽松' },
];

const FRONTEND_VERSION =
  typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '2.0.0';

const FOLDER_ACTIONS = [
  { kind: 'data', label: '数据目录', description: '新版设置、任务日志与本地记录', icon: FolderOpen },
  { kind: 'logs', label: '日志目录', description: '排查问题时使用', icon: FileText },
  { kind: 'output', label: '输出目录', description: '打包结果与导出文件所在位置', icon: Archive },
];

export function SettingsPage({
  data,
  settings,
  settingsBusy,
  saveSettings,
  call,
  refresh,
  refreshing,
  activeJobsCount,
  connection,
  lastUpdated,
}) {
  const toast = useToast();
  const [folderPending, setFolderPending] = useState(null);
  const [legacyPending, setLegacyPending] = useState(false);
  const [settingError, setSettingError] = useState(null);
  const app = data.app || {};
  const warnings = data.warnings || [];

  async function handleTheme(theme) {
    if (theme === settings.theme || settingsBusy) return;
    setSettingError(null);
    const result = await saveSettings({ theme });
    if (!result.ok) {
      setSettingError(result.error);
      toast({ tone: 'error', title: '主题未保存', message: result.error });
    }
  }

  async function handleFontScale(value) {
    if (value === settings.font_scale || settingsBusy) return;
    setSettingError(null);
    const result = await saveSettings({ font_scale: value });
    if (!result.ok) {
      setSettingError(result.error);
      toast({ tone: 'error', title: '字号未保存', message: result.error });
    }
  }

  async function handleOpenFolder(kind) {
    setFolderPending(kind);
    const result = await call('open_folder', { kind });
    setFolderPending(null);
    if (!result.ok) {
      toast({ tone: 'error', title: '无法打开目录', message: result.error });
      return;
    }
    toast({
      tone: 'success',
      title: '已请求打开目录',
      message: (result.data && result.data.message) || FOLDER_ACTIONS.find((item) => item.kind === kind)?.label || '本地目录',
    });
  }

  async function handleOpenLegacy() {
    setLegacyPending(true);
    const result = await call('launch_tool', { id: 'legacy' });
    setLegacyPending(false);
    if (!result.ok) {
      toast({ tone: 'error', title: '无法打开旧版', message: result.error });
      return;
    }
    const action = result.data && result.data.action;
    toast({
      tone: action === 'pending' ? 'info' : 'success',
      title: action === 'focused' ? '已切换到旧版窗口' : '已请求打开旧版',
      message: (result.data && result.data.message) || '旧版启动器仍然保留，可随时回退。',
    });
  }

  return (
    <div className="page settings-page">
      <PageHeader
        eyebrow="设置"
        title="外观与本地服务"
        description="主题与字号立即生效并保存到本地。数据、日志和旧版入口都通过本地服务打开。"
        actions={
          <Button
            variant="secondary"
            icon={RefreshCw}
            loading={settingsBusy || refreshing}
            onClick={async () => {
              const result = await refresh();
              if (result.ok) {
                toast({ tone: 'success', title: '设置与数据已刷新' });
              }
            }}
          >
            刷新数据
          </Button>
        }
      />

      {settingError ? (
        <InlineAlert tone="error" title="设置保存失败" onDismiss={() => setSettingError(null)}>
          {settingError}
        </InlineAlert>
      ) : null}

      <div className="settings-layout">
        <div className="settings-main">
          <section className="panel settings-section" aria-labelledby="settings-theme-title">
            <SectionHeader
              id="settings-theme-title"
              title="主题"
              description="界面会立即切换；保存失败时会恢复原来的主题。"
              action={
                settingsBusy ? (
                  <span className="save-state save-state--saving">
                    <Spinner size={13} /> 保存中
                  </span>
                ) : (
                  <span className="save-state save-state--saved">
                    <Check size={13} /> 已保存
                  </span>
                )
              }
            />
            <div className="option-grid" role="radiogroup" aria-label="主题">
              {THEME_OPTIONS.map((option) => {
                const Icon = option.icon;
                const active = settings.theme === option.id;
                return (
                  <button
                    key={option.id}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    className={`option-card ${active ? 'is-active' : ''}`.trim()}
                    onClick={() => handleTheme(option.id)}
                    disabled={settingsBusy}
                  >
                    <span className={`option-card__preview option-card__preview--${option.id}`}>
                      <span className="option-card__sidebar" />
                      <span className="option-card__content">
                        <span />
                        <span />
                        <span />
                      </span>
                    </span>
                    <span className="option-card__text">
                      <strong>
                        <Icon size={15} aria-hidden="true" /> {option.label}
                      </strong>
                      <small>{option.description}</small>
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="panel settings-section" aria-labelledby="settings-font-title">
            <SectionHeader
              id="settings-font-title"
              title="界面字号"
              description="影响整体文字与控件尺寸，选择后立即保存。"
            />
            <div className="font-options" role="radiogroup" aria-label="界面字号">
              {FONT_OPTIONS.map((option) => {
                const active = Number(settings.font_scale) === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    className={`font-option ${active ? 'is-active' : ''}`.trim()}
                    onClick={() => handleFontScale(option.value)}
                    disabled={settingsBusy}
                  >
                    <span className="font-option__sample" style={{ fontSize: `${option.value * 16}px` }}>
                      Aa
                    </span>
                    <strong>{option.label}</strong>
                    <small>
                      {option.value === 1 ? '100%' : `${Math.round(option.value * 100)}%`} · {option.sample}
                    </small>
                  </button>
                );
              })}
            </div>
            <p className="settings-note">
              当前倍率 {Math.round(Number(settings.font_scale) * 100)}%。窄窗口下布局会自动变为单列，
              不依赖缩放。
            </p>
          </section>

          <section className="panel settings-section" aria-labelledby="settings-folders-title">
            <SectionHeader
              id="settings-folders-title"
              title="本地目录"
              description="只打开后端配置的目录，不接受任意文件路径。"
            />
            <div className="folder-list">
              {FOLDER_ACTIONS.map((item) => {
                const Icon = item.icon;
                return (
                  <div className="folder-row" key={item.kind}>
                    <span className="folder-row__icon" aria-hidden="true">
                      <Icon size={19} />
                    </span>
                    <div>
                      <strong>{item.label}</strong>
                      <p>{item.description}</p>
                    </div>
                    <Button
                      size="sm"
                      variant="secondary"
                      loading={folderPending === item.kind}
                      onClick={() => handleOpenFolder(item.kind)}
                    >
                      打开
                    </Button>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="panel settings-section" aria-labelledby="settings-legacy-title">
            <SectionHeader
              id="settings-legacy-title"
              title="旧版入口"
              description="新版与旧版并存。旧版只在你点击时打开。"
            />
            <div className="legacy-row">
              <span className="legacy-row__icon" aria-hidden="true">
                <Archive size={20} />
              </span>
              <div>
                <strong>旧版个人工具中心</strong>
                <p>保留原来的工具入口，便于验证或回退。不会替换或清空任何旧数据。</p>
              </div>
              <Button
                variant="secondary"
                icon={FolderOpen}
                loading={legacyPending}
                onClick={handleOpenLegacy}
              >
                打开旧版
              </Button>
            </div>
          </section>
        </div>

        <aside className="settings-side">
          <section className="panel settings-section" aria-labelledby="settings-about-title">
            <SectionHeader id="settings-about-title" title="关于" description="版本与运行环境" />
            <dl className="info-list">
              <div>
                <dt>软件</dt>
                <dd>{app.name || '个人工具中心'}</dd>
              </div>
              <div>
                <dt>后端版本</dt>
                <dd>{app.version || '未知'}</dd>
              </div>
              <div>
                <dt>前端构建</dt>
                <dd>{FRONTEND_VERSION}</dd>
              </div>
              <div>
                <dt>平台</dt>
                <dd>{app.platform || 'Windows'}</dd>
              </div>
              <div>
                <dt>连接</dt>
                <dd>
                  <Badge tone={connection === 'ready' ? 'success' : 'warning'} dot>
                    {connection === 'ready' ? '本地服务已连接' : '连接状态异常'}
                  </Badge>
                </dd>
              </div>
              <div>
                <dt>最近同步</dt>
                <dd>{lastUpdated ? formatDateTime(lastUpdated) : '尚未同步'}</dd>
              </div>
              <div>
                <dt>活动任务</dt>
                <dd>{activeJobsCount} 个</dd>
              </div>
            </dl>
            <p className="settings-note">
              2.0 采用全新界面，保留原有 Python / C++ 工具与数据位置。
              软件不包含上传、云同步或自动更新功能；界面资源随本地构建一起加载，不使用 CDN。
            </p>
          </section>

          <section className="panel settings-section" aria-labelledby="settings-diagnostics-title">
            <SectionHeader id="settings-diagnostics-title" title="本地服务" description="必要时可重新加载数据" />
            <div className="diagnostic-row">
              <span className="diagnostic-row__icon" aria-hidden="true">
                <Server size={18} />
              </span>
              <div>
                <strong>{connection === 'ready' ? '本地服务已就绪' : '等待连接'}</strong>
                <p>
                  界面通过本地服务打开文件、工具与游戏。失败时会显示中文提示，
                  不会把失败显示成成功。
                </p>
              </div>
            </div>
            <Button
              variant="secondary"
              icon={RefreshCw}
              loading={refreshing}
              onClick={async () => {
                const result = await refresh();
                if (result.ok) toast({ tone: 'success', title: '已重新载入本地数据' });
              }}
            >
              重新载入数据
            </Button>
          </section>

          {warnings.length ? (
            <section className="panel settings-section" aria-labelledby="settings-warnings-title">
              <SectionHeader id="settings-warnings-title" title="启动提醒" />
              <ul className="warning-list">
                {warnings.map((warning, index) => (
                  <li key={`${index}-${String(warning).slice(0, 20)}`}>
                    <TriangleAlert size={15} aria-hidden="true" />
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section className="panel settings-section" aria-labelledby="settings-help-title">
            <SectionHeader id="settings-help-title" title="快捷键" />
            <div className="shortcut-row">
              <span>全局检索</span>
              <span>
                <kbd>Ctrl</kbd> + <kbd>K</kbd>
              </span>
            </div>
            <div className="shortcut-row">
              <span>关闭搜索 / 对话框</span>
              <span>
                <kbd>Esc</kbd>
              </span>
            </div>
            <div className="shortcut-row">
              <span>搜索结果选择</span>
              <span>
                <kbd>↑</kbd> <kbd>↓</kbd> <kbd>Enter</kbd>
              </span>
            </div>
            <p className="settings-note">
              页面加载、输入搜索或切换导航都不会自动启动游戏与修改器。
            </p>
          </section>

          <div className="about-stamp">
            <Settings2 size={18} aria-hidden="true" />
            <div>
              <strong>个人工具中心 2.0</strong>
              <span>本地运行 · 不上传 · 保留旧版</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
