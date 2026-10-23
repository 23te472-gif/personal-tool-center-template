/** 文件选择、打包任务与轮询相关的纯逻辑。 */

export function normalizePathKey(path) {
  return String(path == null ? '' : path).replace(/\//g, '\\').toLocaleLowerCase('en-US');
}

export function isValidFile(file) {
  return Boolean(file && typeof file === 'object' && typeof file.path === 'string' && file.path.trim());
}

/** 追加新选择并去重；Windows 路径按不区分大小写处理。保留已有顺序。 */
export function mergePickedFiles(existing, incoming) {
  const base = Array.isArray(existing) ? existing.filter(isValidFile) : [];
  const next = Array.isArray(incoming) ? incoming.filter(isValidFile) : [];
  const seen = new Set(base.map((file) => normalizePathKey(file.path)));
  const merged = [...base];
  for (const file of next) {
    const key = normalizePathKey(file.path);
    if (seen.has(key)) continue;
    seen.add(key);
    merged.push(file);
  }
  return merged;
}

export function removeFile(files, path) {
  const list = Array.isArray(files) ? files : [];
  const key = normalizePathKey(path);
  return list.filter((file) => normalizePathKey(file.path) !== key);
}

export function totalFileSize(files) {
  const list = Array.isArray(files) ? files : [];
  return list.reduce((total, file) => {
    const size = Number(file && file.size);
    return total + (Number.isFinite(size) && size > 0 ? size : 0);
  }, 0);
}

export function missingFiles(files) {
  const list = Array.isArray(files) ? files : [];
  return list.filter((file) => file && file.exists === false);
}

export function hasMissingFiles(files) {
  return missingFiles(files).length > 0;
}

/** 按契约组装 pack_start 参数；输出目录为空时交给后端默认目录。 */
export function buildPackPayload(files, outputDir) {
  const list = Array.isArray(files) ? files.filter(isValidFile) : [];
  const payload = { files: list.map((file) => file.path) };
  const dir = String(outputDir == null ? '' : outputDir).trim();
  if (dir) payload.output_dir = dir;
  return payload;
}

export function canStartPack(files, { busy = false } = {}) {
  const list = Array.isArray(files) ? files : [];
  return !busy && list.length > 0 && !hasMissingFiles(list);
}

export function jobStatusLabel(status) {
  switch (status) {
    case 'queued':
      return '排队中';
    case 'running':
      return '进行中';
    case 'completed':
      return '已完成';
    case 'failed':
      return '失败';
    default:
      return '未知状态';
  }
}
