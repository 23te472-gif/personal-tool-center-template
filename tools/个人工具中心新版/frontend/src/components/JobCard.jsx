import { CheckCircle2, ExternalLink, FolderOpen, Loader2, TriangleAlert } from 'lucide-react';
import { jobStatusLabel } from '../lib/pack.js';
import { isActiveJob } from '../lib/jobs.js';
import { Badge, Button } from './ui.jsx';

const STATUS_TONES = {
  queued: 'neutral',
  running: 'info',
  completed: 'success',
  failed: 'danger',
};

export function JobStatusBadge({ status }) {
  return (
    <Badge tone={STATUS_TONES[status] || 'neutral'} dot>
      {jobStatusLabel(status)}
    </Badge>
  );
}

export function progressValue(job) {
  const raw = Number(job && job.progress);
  if (!Number.isFinite(raw)) return 0;
  return Math.min(100, Math.max(0, Math.round(raw)));
}

export function JobProgressBar({ job, labelled = true }) {
  const value = progressValue(job);
  const active = isActiveJob(job);
  return (
    <div className="job-progress">
      <div
        className={`job-progress__track ${active && value === 0 ? 'is-indeterminate' : ''}`.trim()}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value}
        aria-label={job && job.message ? `打包进度：${job.message}` : '打包进度'}
      >
        <span className="job-progress__bar" style={{ width: `${value}%` }} />
      </div>
      {labelled ? (
        <div className="job-progress__meta">
          <span>{job && job.message ? job.message : '等待任务状态…'}</span>
          <strong>{value}%</strong>
        </div>
      ) : null}
    </div>
  );
}

export function JobRow({ job, onOpen, onGoPack, onRetry }) {
  const completed = job.status === 'completed';
  const failed = job.status === 'failed';
  return (
    <article className={`job-row job-row--${job.status || 'unknown'}`}>
      <div className="job-row__head">
        <div className="job-row__title">
          {isActiveJob(job) ? (
            <Loader2 size={16} className="spinner" aria-hidden="true" />
          ) : completed ? (
            <CheckCircle2 size={16} className="text-success" aria-hidden="true" />
          ) : failed ? (
            <TriangleAlert size={16} className="text-danger" aria-hidden="true" />
          ) : (
            <FolderOpen size={16} aria-hidden="true" />
          )}
          <span>任务 {String(job.id).slice(0, 12)}</span>
        </div>
        <JobStatusBadge status={job.status} />
      </div>
      {isActiveJob(job) ? <JobProgressBar job={job} /> : null}
      {completed ? (
        <div className="job-row__result">
          <div>
            <span className="muted">已完成</span>
            {job.result_path ? <code title={job.result_path}>{job.result_path}</code> : null}
          </div>
          {onOpen ? (
            <Button size="sm" variant="secondary" icon={ExternalLink} onClick={() => onOpen(job)}>
              打开所在位置
            </Button>
          ) : null}
        </div>
      ) : null}
      {failed ? (
        <div className="job-row__error">
          <p>{job.error || job.message || '任务未能完成，请重试。'}</p>
          <div className="job-row__error-actions">
            {onRetry ? (
              <Button size="sm" variant="secondary" onClick={() => onRetry(job)}>
                重新尝试
              </Button>
            ) : null}
            {onGoPack ? (
              <Button size="sm" variant="ghost" onClick={onGoPack}>
                前往文件打包
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}
    </article>
  );
}
