import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { BRIDGE_UNAVAILABLE, createBridge } from '../lib/bridge.js';
import {
  getActiveJobs,
  JOB_POLL_INTERVAL_MS,
  upsertJob,
} from '../lib/jobs.js';

const EMPTY_SETTINGS = { theme: 'light', font_scale: 1 };

function isValidSnapshot(snapshot) {
  return Boolean(
    snapshot &&
      typeof snapshot === 'object' &&
      !Array.isArray(snapshot) &&
      snapshot.app &&
      typeof snapshot.app === 'object' &&
      Array.isArray(snapshot.tools) &&
      Array.isArray(snapshot.games)
  );
}

function normalizeSnapshot(snapshot) {
  return {
    ...snapshot,
    tools: snapshot.tools,
    games: snapshot.games,
    jobs: Array.isArray(snapshot.jobs) ? snapshot.jobs : [],
    warnings: Array.isArray(snapshot.warnings) ? snapshot.warnings : [],
    recent: Array.isArray(snapshot.recent) ? snapshot.recent : [],
    materials:
      snapshot.materials && typeof snapshot.materials === 'object'
        ? snapshot.materials
        : {},
    wheel:
      snapshot.wheel && typeof snapshot.wheel === 'object'
        ? {
            entries: Array.isArray(snapshot.wheel.entries) ? snapshot.wheel.entries : [],
            recent: Array.isArray(snapshot.wheel.recent) ? snapshot.wheel.recent : [],
            exclude_recent: Boolean(snapshot.wheel.exclude_recent),
            challenge: snapshot.wheel.challenge,
          }
        : { entries: [], recent: [], exclude_recent: false, challenge: null },
    settings:
      snapshot.settings && typeof snapshot.settings === 'object'
        ? {
            theme: snapshot.settings.theme === 'dark' ? 'dark' : 'light',
            font_scale: [0.9, 1, 1.15].includes(Number(snapshot.settings.font_scale))
              ? Number(snapshot.settings.font_scale)
              : 1,
          }
        : { ...EMPTY_SETTINGS },
    pack:
      snapshot.pack && typeof snapshot.pack === 'object'
        ? {
            files: Array.isArray(snapshot.pack.files) ? snapshot.pack.files : [],
            output_dir:
              typeof snapshot.pack.output_dir === 'string' ? snapshot.pack.output_dir : '',
          }
        : { files: [], output_dir: '' },
  };
}

/**
 * 应用级数据与 bridge 生命周期。
 * - 只在 pywebviewready / bridge 可用后执行一次 bootstrap。
 * - 失败不伪装成功，也不无限重试 bootstrap；用户可显式重试。
 * - 仅当存在 queued/running 任务时以 1 秒间隔轮询 job_status。
 */
export function useToolCenter() {
  const bridge = useMemo(
    () => createBridge(typeof window === 'undefined' ? undefined : window),
    []
  );
  const [data, setData] = useState(null);
  const [connection, setConnection] = useState('connecting');
  const [connectionError, setConnectionError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [jobPollError, setJobPollError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [settingsBusy, setSettingsBusy] = useState(false);
  const [packDraft, setPackDraft] = useState({ files: [], output_dir: '' });
  const [lastPackJobId, setLastPackJobId] = useState(null);

  const dataRef = useRef(null);
  const mountedRef = useRef(true);
  const loadInFlightRef = useRef(false);
  const hasTriedRef = useRef(false);
  const initialPackLoadedRef = useRef(false);
  const settingsBusyRef = useRef(false);

  const updateData = useCallback((updater) => {
    setData((current) => {
      const next = typeof updater === 'function' ? updater(current) : updater;
      dataRef.current = next;
      return next;
    });
  }, []);

  const applySnapshot = useCallback((raw) => {
    const snapshot = normalizeSnapshot(raw);
    dataRef.current = snapshot;
    setData(snapshot);
    setJobs(snapshot.jobs);
    setPackDraft((current) => {
      if (initialPackLoadedRef.current) return current;
      initialPackLoadedRef.current = true;
      return {
        files: snapshot.pack.files,
        output_dir: snapshot.pack.output_dir,
      };
    });
    setConnection('ready');
    setConnectionError(null);
    setRefreshError(null);
    setLastUpdated(new Date().toISOString());
  }, []);

  const load = useCallback(
    async ({ refresh = false } = {}) => {
      if (loadInFlightRef.current) {
        return { ok: false, error: '数据正在刷新，请稍候。' };
      }
      loadInFlightRef.current = true;
      if (refresh) {
        setRefreshing(true);
        setRefreshError(null);
      } else if (!dataRef.current) {
        setConnection('connecting');
        setConnectionError(null);
      }

      const result = await bridge.call('bootstrap', {});
      loadInFlightRef.current = false;
      if (!mountedRef.current) return result;

      if (result.ok) {
        if (!isValidSnapshot(result.data)) {
          const message = '本地服务返回的数据不完整，暂时无法显示工作台。请重试或重新打开应用。';
          if (dataRef.current) setRefreshError(message);
          else {
            setConnection('error');
            setConnectionError(message);
          }
          return { ok: false, error: message };
        }
        applySnapshot(result.data);
        return result;
      }

      if (dataRef.current) {
        setRefreshError(result.error);
        setConnection('ready');
      } else {
        setConnection('error');
        setConnectionError(result.error);
      }
      return result;
    },
    [applySnapshot, bridge]
  );

  const retry = useCallback(async () => {
    hasTriedRef.current = false;
    setRefreshError(null);
    setConnectionError(null);
    if (!bridge.isAvailable()) {
      setConnection('error');
      setConnectionError(BRIDGE_UNAVAILABLE);
      return { ok: false, error: BRIDGE_UNAVAILABLE };
    }
    hasTriedRef.current = true;
    return load({ refresh: Boolean(dataRef.current) });
  }, [bridge, load]);

  const clearRefreshError = useCallback(() => setRefreshError(null), []);

  useEffect(() => {
    mountedRef.current = true;
    let disposed = false;

    const attempt = () => {
      if (disposed || hasTriedRef.current || !bridge.isAvailable()) return;
      hasTriedRef.current = true;
      load({});
    };

    const onReady = () => {
      if (!disposed) attempt();
    };

    window.addEventListener('pywebviewready', onReady);
    const initialTimer = window.setTimeout(attempt, 0);
    const bridgeProbe = window.setInterval(attempt, 900);

    return () => {
      disposed = true;
      mountedRef.current = false;
      window.clearTimeout(initialTimer);
      window.clearInterval(bridgeProbe);
      window.removeEventListener('pywebviewready', onReady);
    };
  }, [bridge, load]);

  const refresh = useCallback(async () => {
    if (!bridge.isAvailable()) {
      const error = BRIDGE_UNAVAILABLE;
      if (dataRef.current) setRefreshError(error);
      else {
        setConnection('error');
        setConnectionError(error);
      }
      return { ok: false, error };
    }
    return load({ refresh: true });
  }, [bridge, load]);

  const activeJobs = getActiveJobs(jobs);
  const activeJobIds = activeJobs.map((job) => job.id).join('|');

  useEffect(() => {
    if (!activeJobIds) {
      setJobPollError(null);
      return undefined;
    }
    let disposed = false;
    let timer = null;
    const ids = activeJobIds.split('|').filter(Boolean);

    const tick = async () => {
      const results = await Promise.all(
        ids.map((id) => bridge.call('job_status', { id }))
      );
      if (disposed) return;
      let hadError = false;
      for (const result of results) {
        const job = result.ok && result.data ? result.data.job : null;
        if (job && job.id) setJobs((current) => upsertJob(current, job));
        else hadError = true;
      }
      setJobPollError(
        hadError ? '任务状态暂时无法更新，正在重试；不会把未确认的任务显示为完成。' : null
      );
      timer = window.setTimeout(tick, JOB_POLL_INTERVAL_MS);
    };

    timer = window.setTimeout(tick, JOB_POLL_INTERVAL_MS);
    return () => {
      disposed = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [activeJobIds, bridge]);

  const updateGames = useCallback(
    (games) => updateData((current) => (current ? { ...current, games: games || [] } : current)),
    [updateData]
  );

  const updateMaterials = useCallback(
    (materials) =>
      updateData((current) =>
        current ? { ...current, materials: materials || {} } : current
      ),
    [updateData]
  );

  const updateWheel = useCallback(
    (wheel) =>
      updateData((current) => (current ? { ...current, wheel } : current)),
    [updateData]
  );

  const updateSettings = useCallback(
    (settings) =>
      updateData((current) => (current ? { ...current, settings } : current)),
    [updateData]
  );

  const addOrUpdateJob = useCallback((job) => {
    if (!job || !job.id) return;
    setJobs((current) => upsertJob(current, job));
    setLastPackJobId(job.id);
  }, []);

  const saveSettings = useCallback(
    async (patch) => {
      const current = dataRef.current;
      if (!current || settingsBusyRef.current) {
        return { ok: false, error: '暂无可保存的设置，请稍候。' };
      }
      const previous = current.settings || EMPTY_SETTINGS;
      const next = {
        theme: patch.theme === 'dark' ? 'dark' : patch.theme === 'light' ? 'light' : previous.theme,
        font_scale: [0.9, 1, 1.15].includes(Number(patch.font_scale))
          ? Number(patch.font_scale)
          : previous.font_scale,
      };
      settingsBusyRef.current = true;
      setSettingsBusy(true);
      updateSettings(next);

      const result = await bridge.call('settings_save', {
        theme: next.theme,
        font_scale: next.font_scale,
      });
      settingsBusyRef.current = false;
      if (!mountedRef.current) return result;
      setSettingsBusy(false);
      if (result.ok) {
        if (
          result.data &&
          result.data.settings &&
          typeof result.data.settings === 'object'
        ) {
          updateSettings({
            theme: result.data.settings.theme === 'dark' ? 'dark' : 'light',
            font_scale: [0.9, 1, 1.15].includes(Number(result.data.settings.font_scale))
              ? Number(result.data.settings.font_scale)
              : next.font_scale,
          });
        }
        return result;
      }
      updateSettings(previous);
      return result;
    },
    [bridge, updateSettings]
  );

  const settings = (data && data.settings) || EMPTY_SETTINGS;

  return {
    bridge,
    call: bridge.call,
    data,
    settings,
    connection,
    connectionError,
    refreshing,
    refreshError,
    jobs,
    jobPollError,
    lastUpdated,
    settingsBusy,
    packDraft,
    setPackDraft,
    lastPackJobId,
    setLastPackJobId,
    activeJobs,
    refresh,
    retry,
    clearRefreshError,
    saveSettings,
    updateGames,
    updateMaterials,
    updateWheel,
    updateSettings,
    addOrUpdateJob,
  };
}
