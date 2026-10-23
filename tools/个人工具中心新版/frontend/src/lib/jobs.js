/** 任务状态与轮询判断。仅在存在 queued/running 任务时轮询。 */

export const ACTIVE_JOB_STATUSES = new Set(['queued', 'running']);
export const TERMINAL_JOB_STATUSES = new Set(['completed', 'failed']);

export function isActiveJob(job) {
  return Boolean(job && ACTIVE_JOB_STATUSES.has(job.status));
}

export function isTerminalJob(job) {
  return Boolean(job && TERMINAL_JOB_STATUSES.has(job.status));
}

export function getActiveJobs(jobs) {
  return Array.isArray(jobs) ? jobs.filter(isActiveJob) : [];
}

export function getActiveJobIds(jobs) {
  return getActiveJobs(jobs).map((job) => job.id);
}

/** 契约里的 progress 按 0–100 百分比解释，并做边界保护。 */
export function jobProgress(job) {
  const raw = Number(job && job.progress);
  if (!Number.isFinite(raw)) return 0;
  return Math.min(100, Math.max(0, Math.round(raw)));
}

export function shouldPollJobs(jobs) {
  return getActiveJobs(jobs).length > 0;
}

/** 轮询间隔 1000ms，位于契约建议的 800–1200ms 区间。 */
export const JOB_POLL_INTERVAL_MS = 1000;

export function upsertJob(jobs, job) {
  const list = Array.isArray(jobs) ? jobs : [];
  if (!job || !job.id) return list;
  const index = list.findIndex((item) => item.id === job.id);
  if (index === -1) return [...list, job];
  const next = [...list];
  next[index] = { ...list[index], ...job };
  return next;
}

export function latestJob(jobs) {
  const list = Array.isArray(jobs) ? jobs : [];
  return list.length ? list[list.length - 1] : null;
}

export function findJob(jobs, id) {
  if (!id) return null;
  return (Array.isArray(jobs) ? jobs : []).find((job) => job.id === id) || null;
}
