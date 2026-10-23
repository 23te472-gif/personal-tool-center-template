import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Archive,
  ArrowRight,
  FileText,
  FolderOpen,
  History,
  Package,
  Plus,
  Trash2,
  TriangleAlert,
  X,
} from 'lucide-react';
import {
  buildPackPayload,
  canStartPack,
  hasMissingFiles,
  mergePickedFiles,
  missingFiles,
  removeFile,
  totalFileSize,
} from '../lib/pack.js';
import { isActiveJob, findJob } from '../lib/jobs.js';
import { formatBytes, truncateMiddle } from '../lib/format.js';
import { MATERIAL_LABELS } from '../lib/search.js';
import { useToast } from '../components/Toasts.jsx';
import {
  Badge,
  Button,
  EmptyState,
  IconButton,
  InlineAlert,
  PageHeader,
  SectionHeader,
} from '../components/ui.jsx';
import { MaterialIcon } from '../components/ToolIcon.jsx';
import { JobRow, JobStatusBadge, JobProgressBar } from '../components/JobCard.jsx';

const QUICK_MATERIALS = ['thesis', 'presentation'];

export function PackPage({
  data,
  jobs,
  jobPollError,
  call,
  packDraft,
  setPackDraft,
  updateMaterials,
  lastPackJobId,
  addOrUpdateJob,
  focusMaterialId,
  onFocusConsumed,
}) {
  const toast = useToast();
  const [pending, setPending] = useState(null);
  const [materialPending, setMaterialPending] = useState(null);
  const [pageError, setPageError] = useState(null);
  const [highlightedMaterial, setHighlightedMaterial] = useState(null);
  const highlightTimerRef = useRef(null);

  const files = packDraft.files || [];
  const outputDir = packDraft.output_dir || '';
  const missing = missingFiles(files);
  const startable = canStartPack(files, { busy: Boolean(pending) });
  const activeJobs = jobs.filter(isActiveJob);
  const recentJobs = jobs.filter((job) => !isActiveJob(job)).slice(-3).reverse();
  const focusedJob = findJob(jobs, lastPackJobId);
  const materials = data.materials || {};
  const configuredMaterials = QUICK_MATERIALS.filter((id) => {
    const material = materials[id];
    return Boolean(material && material.path && material.exists !== false);
  });

  useEffect(() => {
    if (!focusMaterialId) return undefined;
    setHighlightedMaterial(focusMaterialId);
    const node = document.querySelector(
      `[data-material-id="${String(focusMaterialId).replace(/"/g, '\\"')}"]`
    );
    if (node && typeof node.scrollIntoView === 'function') {
      node.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
    if (highlightTimerRef.current) window.clearTimeout(highlightTimerRef.current);
    highlightTimerRef.current = window.setTimeout(() => setHighlightedMaterial(null), 2600);
    if (onFocusConsumed) onFocusConsumed();
    return () => {
      if (highlightTimerRef.current) window.clearTimeout(highlightTimerRef.current);
    };
    // 只在外部深链变化时处理。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusMaterialId]);

  const sizeLabel = useMemo(() => formatBytes(totalFileSize(files)), [files]);

  function setFiles(nextFiles, nextOutput = outputDir) {
    setPackDraft({ files: nextFiles, output_dir: nextOutput });
  }

  async function handlePickFiles() {
    setPending('files');
    setPageError(null);
    const result = await call('pick_files', {});
    setPending(null);
    if (!result.ok) {
      setPageError(result.error);
      return;
    }
    if (result.data && result.data.cancelled) return;
    const incoming = result.data && Array.isArray(result.data.files) ? result.data.files : [];
    const merged = mergePickedFiles(files, incoming);
    setFiles(merged);
    const added = merged.length - files.length;
    if (added > 0) {
      toast({
        tone: 'success',
        title: '已加入打包列表',
        message: `新增 ${added} 个文件${incoming.length > added ? `，跳过 ${incoming.length - added} 个重复项` : ''}。`,
      });
    } else {
      toast({ tone: 'info', title: '没有新增文件', message: '所选文件已在列表中。' });
    }
  }

  async function handlePrevious() {
    setPending('previous');
    setPageError(null);
    const result = await call('pack_previous', {});
    setPending(null);
    if (!result.ok) {
      setPageError(result.error);
      return;
    }
    const previousFiles = result.data && Array.isArray(result.data.files) ? result.data.files : [];
    const previousOutput = (result.data && result.data.output_dir) || '';
    if (!previousFiles.length && !previousOutput) {
      toast({ tone: 'info', title: '暂无可重用的上次选择', message: '先选择文件并完成一次打包。' });
      return;
    }
    setPackDraft({ files: previousFiles, output_dir: previousOutput });
    toast({
      tone: 'success',
      title: '已载入上次选择',
      message: `${previousFiles.length} 个文件${previousOutput ? '与上次输出目录' : ''}。`,
    });
  }

  async function handlePickOutput() {
    setPending('output');
    setPageError(null);
    const result = await call('pick_output', {});
    setPending(null);
    if (!result.ok) {
      setPageError(result.error);
      return;
    }
    if (result.data && result.data.cancelled) return;
    const path = result.data && result.data.path;
    if (path) {
      setPackDraft((current) => ({ ...current, output_dir: path }));
      toast({ tone: 'info', title: '输出目录已选择', message: path });
    }
  }

  async function handleStartPack() {
    if (!files.length) return;
    setPending('start');
    setPageError(null);
    const result = await call('pack_start', buildPackPayload(files, outputDir));
    setPending(null);
    if (!result.ok) {
      setPageError(result.error);
      toast({ tone: 'error', title: '无法开始打包', message: result.error });
      return;
    }
    const job = result.data && result.data.job;
    if (job) addOrUpdateJob(job);
    toast({
      tone: 'success',
      title: '打包任务已开始',
      message: '任务在本地运行，进度会实时更新。',
    });
  }

  async function handleMaterialChoose(id) {
    setMaterialPending(id);
    const result = await call('materials_choose', { id });
    setMaterialPending(null);
    if (!result.ok) {
      toast({ tone: 'error', title: '无法选择资料', message: result.error });
      return;
    }
    if (result.data && result.data.cancelled) return;
    if (result.data && result.data.materials) updateMaterials(result.data.materials);
    toast({ tone: 'success', title: '资料入口已更新', message: MATERIAL_LABELS[id] || '资料' });
  }

  async function handleMaterialOpen(id) {
    setMaterialPending(id);
    const result = await call('materials_open', { id });
    setMaterialPending(null);
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

  async function handlePackMaterials() {
    setPending('materials');
    setPageError(null);
    const payload = outputDir ? { output_dir: outputDir } : {};
    const result = await call('pack_materials', payload);
    setPending(null);
    if (!result.ok) {
      setPageError(result.error);
      toast({ tone: 'error', title: '无法打包资料', message: result.error });
      return;
    }
    const job = result.data && result.data.job;
    if (job) addOrUpdateJob(job);
    toast({
      tone: 'success',
      title: '资料打包任务已开始',
      message: '只打包已配置的论文与演示文稿，进度在下方实时显示。',
    });
  }

  async function handleOpenJob(job) {
    const result = await call('job_open', { id: job.id });
    if (!result.ok) {
      toast({ tone: 'error', title: '无法打开结果位置', message: result.error });
      return;
    }
    toast({
      tone: 'success',
      title: '已请求打开结果位置',
      message: (result.data && result.data.message) || '完成后的 ZIP 所在目录。',
    });
  }

  return (
    <div className="page pack-page">
      <PageHeader
        eyebrow="文件打包"
        title="把文件安全地打成 ZIP"
        description="从原生文件选择器加入文件，可移除、复用上次选择并指定输出目录。文件只在本机处理，不会上传。"
        actions={
          <Button variant="primary" icon={Plus} loading={pending === 'files'} onClick={handlePickFiles}>
            选择文件
          </Button>
        }
      />

      {pageError ? (
        <InlineAlert tone="error" title="打包操作遇到问题" onDismiss={() => setPageError(null)}>
          {pageError}
        </InlineAlert>
      ) : null}

      <div className="pack-layout">
        <div className="pack-main">
          <section className="panel pack-files" aria-labelledby="pack-files-title">
            <SectionHeader
              id="pack-files-title"
              title="待打包文件"
              description={`${files.length} 个文件 · ${sizeLabel}`}
              action={
                <div className="pack-file-actions">
                  <Button
                    size="sm"
                    variant="ghost"
                    icon={History}
                    loading={pending === 'previous'}
                    onClick={handlePrevious}
                  >
                    重用上次选择
                  </Button>
                  {files.length ? (
                    <Button
                      size="sm"
                      variant="ghost"
                      icon={Trash2}
                      onClick={() => setFiles([])}
                    >
                      清空
                    </Button>
                  ) : null}
                </div>
              }
            />

            {files.length ? (
              <ul className="selected-file-list">
                {files.map((file) => {
                  const fileMissing = file.exists === false;
                  return (
                    <li key={file.path} className={fileMissing ? 'is-missing' : ''}>
                      <span className="selected-file__icon" aria-hidden="true">
                        <FileText size={18} />
                      </span>
                      <span className="selected-file__body">
                        <strong>{file.name || file.path}</strong>
                        <code title={file.path}>{truncateMiddle(file.path, 88)}</code>
                      </span>
                      <span className="selected-file__meta">
                        <span className="muted small">{formatBytes(file.size)}</span>
                        {fileMissing ? <Badge tone="danger">不存在</Badge> : null}
                      </span>
                      <IconButton
                        label={`移除 ${file.name || file.path}`}
                        icon={X}
                        size={16}
                        onClick={() => setFiles(removeFile(files, file.path))}
                      />
                    </li>
                  );
                })}
              </ul>
            ) : (
              <EmptyState
                compact
                icon={Package}
                title="还没有选择文件"
                description="使用上方“选择文件”一次加入多个文件，或重用上一次的打包选择。"
                action={
                  <div className="empty-actions">
                    <Button size="sm" variant="secondary" icon={Plus} loading={pending === 'files'} onClick={handlePickFiles}>
                      选择文件
                    </Button>
                    <Button size="sm" variant="ghost" icon={History} loading={pending === 'previous'} onClick={handlePrevious}>
                      重用上次选择
                    </Button>
                  </div>
                }
              />
            )}

            {missing.length ? (
              <InlineAlert tone="warning" title="有文件已不在原位置">
                请移除标为“不存在”的 {missing.length} 个文件后再开始打包；开始按钮已暂时禁用。
              </InlineAlert>
            ) : null}

            <div className="output-row">
              <div className="output-row__icon" aria-hidden="true">
                <FolderOpen size={20} />
              </div>
              <div className="output-row__body">
                <span>输出目录</span>
                <code title={outputDir || ''}>
                  {outputDir || '使用后端默认目录（未手动指定）'}
                </code>
              </div>
              <div className="output-row__actions">
                {outputDir ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setPackDraft((current) => ({ ...current, output_dir: '' }))}
                  >
                    用默认
                  </Button>
                ) : null}
                <Button
                  size="sm"
                  variant="secondary"
                  icon={FolderOpen}
                  loading={pending === 'output'}
                  onClick={handlePickOutput}
                >
                  选择目录
                </Button>
              </div>
            </div>

            <div className="pack-start">
              <div>
                <strong>准备好后开始</strong>
                <p className="muted small">
                  打包在本地执行，关闭窗口前请等待任务完成。
                </p>
              </div>
              <Button
                variant="primary"
                size="lg"
                icon={Archive}
                loading={pending === 'start'}
                disabled={!startable}
                onClick={handleStartPack}
                title={
                  !files.length
                    ? '请先选择文件'
                    : hasMissingFiles(files)
                      ? '请先移除不存在的文件'
                      : '开始本地 ZIP 打包'
                }
              >
                一键开始打包
              </Button>
            </div>
          </section>

          <section className="panel" aria-labelledby="pack-jobs-title">
            <SectionHeader
              id="pack-jobs-title"
              title="任务进度"
              description="打包进行时自动更新，完成后可打开结果位置。"
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
                  <strong>当前没有进行中的打包任务</strong>
                  <p>完成打包后，可在这里打开 ZIP 所在位置。</p>
                </div>
              </div>
            )}

            {recentJobs.length ? (
              <div className="job-stack job-stack--history">
                <div className="job-stack__label">
                  <History size={15} aria-hidden="true" /> 最近任务
                </div>
                {recentJobs.map((job) => (
                  <JobRow key={job.id} job={job} onOpen={handleOpenJob} />
                ))}
              </div>
            ) : null}

            {focusedJob && !activeJobs.some((job) => job.id === focusedJob.id) && !recentJobs.some((job) => job.id === focusedJob.id) ? (
              <div className="job-stack">
                <JobRow job={focusedJob} onOpen={handleOpenJob} />
              </div>
            ) : null}
          </section>
        </div>

        <aside className="pack-side">
          <section className="panel" aria-labelledby="pack-materials-title">
            <SectionHeader
              id="pack-materials-title"
              title="论文与 PPT"
              description="复用已有的资料入口，不需要重复选择文件。"
            />
            <div className="quick-material-list">
              {QUICK_MATERIALS.map((id) => {
                const material = materials[id] || { id };
                const ready = Boolean(material.path && material.exists !== false);
                return (
                  <article className={`quick-material ${ready ? '' : 'is-unconfigured'} ${highlightedMaterial === id ? 'is-highlighted' : ''}`.trim()} key={id} data-material-id={id}>
                    <span className={`material-icon material-icon--${id}`}>
                      <MaterialIcon id={id} />
                    </span>
                    <div className="quick-material__body">
                      <strong>{material.title || MATERIAL_LABELS[id]}</strong>
                      <small title={material.path || ''}>
                        {material.path ? truncateMiddle(material.path, 42) : '尚未配置'}
                      </small>
                      {material.exists === false ? <Badge tone="danger">路径不可用</Badge> : null}
                    </div>
                    <div className="quick-material__actions">
                      <Button
                        size="sm"
                        variant="ghost"
                        loading={materialPending === id}
                        onClick={() => handleMaterialChoose(id)}
                      >
                        {material.path ? '更换' : '选择'}
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        icon={ArrowRight}
                        disabled={!ready || materialPending === id}
                        onClick={() => handleMaterialOpen(id)}
                      >
                        打开
                      </Button>
                    </div>
                  </article>
                );
              })}
            </div>
            <Button
              className="full-width"
              variant="soft"
              icon={Archive}
              loading={pending === 'materials'}
              disabled={!configuredMaterials.length}
              onClick={handlePackMaterials}
              title={
                configuredMaterials.length
                  ? '把已配置的论文和 PPT 打包为 ZIP'
                  : '请先配置至少一项论文或 PPT'
              }
            >
              一键打包论文与 PPT
            </Button>
            <p className="side-note">
              只打包已配置且路径可用的资料。输出目录与上方选择一致；未指定时由后端使用默认目录。
            </p>
          </section>

          <section className="panel privacy-card" aria-labelledby="pack-privacy-title">
            <div className="privacy-card__icon" aria-hidden="true">
              <FolderOpen size={20} />
            </div>
            <h2 id="pack-privacy-title">本地处理</h2>
            <p>
              文件选择、ZIP 打包与打开结果位置都在本机完成。
              界面没有上传接口，也不会把文件路径发送到网络。
            </p>
            <ul>
              <li>取消原生选择器不会报错。</li>
              <li>不存在的文件会先提示移除。</li>
              <li>打包完成后可直接打开结果位置。</li>
            </ul>
          </section>

          {missing.length ? (
            <div className="side-warning">
              <TriangleAlert size={17} aria-hidden="true" />
              <p>{missing.length} 个文件路径已失效，移除后才能开始打包。</p>
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}
