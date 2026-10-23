import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useToolCenter } from './hooks/useToolCenter.js';
import { Sidebar } from './components/Sidebar.jsx';
import { TopBar } from './components/TopBar.jsx';
import { ConnectionScreen } from './components/ConnectionScreen.jsx';
import { ToastProvider, ToastViewport, useToastStore } from './components/Toasts.jsx';
import { Button, InlineAlert } from './components/ui.jsx';
import { Overview } from './pages/Overview.jsx';
import { GamesPage } from './pages/Games.jsx';
import { PackPage } from './pages/Pack.jsx';
import { WheelPage } from './pages/Wheel.jsx';
import { SettingsPage } from './pages/Settings.jsx';

const VALID_PAGES = new Set(['overview', 'games', 'pack', 'wheel', 'settings']);

export default function App() {
  const center = useToolCenter();
  const toastStore = useToastStore();
  const [page, setPage] = useState('overview');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [retryBusy, setRetryBusy] = useState(false);
  const [focusGameId, setFocusGameId] = useState(null);
  const [focusWheelId, setFocusWheelId] = useState(null);
  const [focusToolId, setFocusToolId] = useState(null);
  const [focusMaterialId, setFocusMaterialId] = useState(null);
  const afterLaunchTimer = useRef(null);
  const settings = center.settings;

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = settings.theme === 'dark' ? 'dark' : 'light';
    root.style.setProperty('--font-scale', String(settings.font_scale || 1));
    root.style.colorScheme = settings.theme === 'dark' ? 'dark' : 'light';
  }, [settings.theme, settings.font_scale]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' });
    setMobileNavOpen(false);
  }, [page]);

  useEffect(
    () => () => {
      if (afterLaunchTimer.current) window.clearTimeout(afterLaunchTimer.current);
    },
    []
  );

  const notify = toastStore.notify;

  const navigate = useCallback((nextPage) => {
    if (!VALID_PAGES.has(nextPage)) return;
    setFocusGameId(null);
    setFocusWheelId(null);
    setFocusToolId(null);
    setFocusMaterialId(null);
    setPage(nextPage);
  }, []);

  const handleAfterLaunch = useCallback(() => {
    if (afterLaunchTimer.current) window.clearTimeout(afterLaunchTimer.current);
    afterLaunchTimer.current = window.setTimeout(async () => {
      const result = await center.refresh();
      if (!result.ok) {
        notify({
          tone: 'info',
          title: '最近记录尚未同步',
          message: '启动请求已完成，但刷新最近使用记录失败；可稍后手动刷新。',
        });
      }
    }, 600);
  }, [center, notify]);

  const handleRetry = useCallback(async () => {
    setRetryBusy(true);
    await center.retry();
    setRetryBusy(false);
  }, [center]);

  const handleRefresh = useCallback(async () => {
    const result = await center.refresh();
    if (!result.ok && center.data) {
      notify({ tone: 'error', title: '刷新失败', message: result.error });
    }
  }, [center, notify]);

  const handleToggleTheme = useCallback(async () => {
    const nextTheme = settings.theme === 'dark' ? 'light' : 'dark';
    const result = await center.saveSettings({ theme: nextTheme });
    if (!result.ok) {
      notify({ tone: 'error', title: '主题切换失败', message: result.error });
    }
  }, [center, notify, settings.theme]);

  const handleSearchSelect = useCallback((result) => {
    if (!result) return;
    if (result.type === 'game') {
      setFocusGameId(result.id);
      setPage('games');
      return;
    }
    if (result.type === 'wheel') {
      setFocusWheelId(result.id);
      setPage('wheel');
      return;
    }
    if (result.type === 'material') {
      setFocusMaterialId(result.id);
      setPage('pack');
      return;
    }
    if (result.type === 'tool') {
      if (result.id === 'games') {
        setPage('games');
        return;
      }
      if (result.id === 'delivery') {
        setPage('pack');
        return;
      }
      setFocusToolId(result.id);
      setPage('overview');
    }
  }, []);

  if (!center.data) {
    return (
      <ConnectionScreen
        status={center.connection}
        error={center.connectionError}
        onRetry={handleRetry}
        busy={retryBusy}
      />
    );
  }

  let content = null;
  if (page === 'games') {
    content = (
      <GamesPage
        data={center.data}
        call={center.call}
        updateGames={center.updateGames}
        focusGameId={focusGameId}
        onFocusConsumed={() => setFocusGameId(null)}
        onAfterLaunch={handleAfterLaunch}
      />
    );
  } else if (page === 'pack') {
    content = (
      <PackPage
        data={center.data}
        jobs={center.jobs}
        jobPollError={center.jobPollError}
        call={center.call}
        packDraft={center.packDraft}
        setPackDraft={center.setPackDraft}
        updateMaterials={center.updateMaterials}
        lastPackJobId={center.lastPackJobId}
        addOrUpdateJob={center.addOrUpdateJob}
        focusMaterialId={focusMaterialId}
        onFocusConsumed={() => setFocusMaterialId(null)}
      />
    );
  } else if (page === 'wheel') {
    content = (
      <WheelPage
        data={center.data}
        call={center.call}
        updateWheel={center.updateWheel}
        focusWheelId={focusWheelId}
        onFocusConsumed={() => setFocusWheelId(null)}
      />
    );
  } else if (page === 'settings') {
    content = (
      <SettingsPage
        data={center.data}
        settings={settings}
        settingsBusy={center.settingsBusy}
        saveSettings={center.saveSettings}
        call={center.call}
        refresh={center.refresh}
        refreshing={center.refreshing}
        activeJobsCount={center.activeJobs.length}
        connection={center.connection}
        lastUpdated={center.lastUpdated}
      />
    );
  } else {
    content = (
      <Overview
        data={center.data}
        jobs={center.jobs}
        jobPollError={center.jobPollError}
        lastUpdated={center.lastUpdated}
        onNavigate={navigate}
        onOpenGame={(id) => {
          setFocusGameId(id);
          setPage('games');
        }}
        onPackMaterialJob={center.addOrUpdateJob}
        call={center.call}
        updateMaterials={center.updateMaterials}
        focusToolId={focusToolId}
        onFocusConsumed={() => setFocusToolId(null)}
      />
    );
  }

  return (
    <ToastProvider value={toastStore}>
      <a className="skip-link" href="#main-content">
        跳到主要内容
      </a>
      <div className="app-shell">
        <Sidebar
          page={page}
          onNavigate={navigate}
          mobileOpen={mobileNavOpen}
          onClose={() => setMobileNavOpen(false)}
          activeJobs={center.activeJobs.length}
          connection={center.connection}
          version={center.data.app && center.data.app.version}
        />
        <div className="app-main">
          <TopBar
            data={center.data}
            onSearchSelect={handleSearchSelect}
            onOpenMenu={() => setMobileNavOpen(true)}
            theme={settings.theme}
            onToggleTheme={handleToggleTheme}
            themeBusy={center.settingsBusy}
            onRefresh={handleRefresh}
            refreshing={center.refreshing}
            connection={center.connection}
            lastUpdated={center.lastUpdated}
          />
          {center.refreshError ? (
            <div className="app-banner">
              <InlineAlert
                tone="warning"
                title="刷新数据失败，正在显示上次载入的内容"
                action={
                  <Button
                    size="sm"
                    variant="secondary"
                    icon={RefreshCw}
                    loading={center.refreshing}
                    onClick={handleRefresh}
                  >
                    重试
                  </Button>
                }
                onDismiss={center.clearRefreshError}
              >
                {center.refreshError}
              </InlineAlert>
            </div>
          ) : null}
          <main className="page-scroll" id="main-content" tabIndex={-1}>
            <div key={page} className="page-transition">
              {content}
            </div>
          </main>
        </div>
        <ToastViewport toasts={toastStore.toasts} onDismiss={toastStore.dismiss} />
      </div>
    </ToastProvider>
  );
}
