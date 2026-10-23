/** 文本、字节、时间与游戏资料表单的纯函数工具。 */

export function normalizeText(value) {
  return String(value == null ? '' : value)
    .normalize('NFKC')
    .toLocaleLowerCase('zh-CN')
    .replace(/\s+/g, ' ')
    .trim();
}

export function formatBytes(bytes) {
  const value = Number(bytes);
  if (!Number.isFinite(value) || value <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = value;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  const digits = unit === 0 || size >= 100 ? 0 : size >= 10 ? 1 : 2;
  const fixed = size.toFixed(digits);
  const text = digits > 0 ? fixed.replace(/\.?0+$/, '') : fixed;
  return `${text} ${units[unit]}`;
}

export function formatNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '0';
  return new Intl.NumberFormat('zh-CN').format(number);
}

export function formatDateTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function formatRecentTime(value) {
  if (!value) return '';
  const text = String(value);
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) return text;
  const delta = Date.now() - date.getTime();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (delta >= 0 && delta < minute) return '刚刚';
  if (delta >= minute && delta < hour) return `${Math.floor(delta / minute)} 分钟前`;
  if (delta >= hour && delta < day) return `${Math.floor(delta / hour)} 小时前`;
  if (delta >= day && delta < 7 * day) return `${Math.floor(delta / day)} 天前`;
  return formatDateTime(text);
}

/** 中文逗号、英文逗号、分号、换行均可分隔别名；去空并按不区分大小写去重。 */
export function parseAliases(input) {
  const pieces = String(input == null ? '' : input)
    .split(/[,，;；\n\r]+/)
    .map((item) => item.trim())
    .filter(Boolean);
  const seen = new Set();
  const result = [];
  for (const piece of pieces) {
    const key = normalizeText(piece);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    result.push(piece);
  }
  return result;
}

export function aliasesToText(aliases) {
  return Array.isArray(aliases) ? aliases.join('、') : '';
}

export function normalizeSteamAppId(value) {
  const text = String(value == null ? '' : value).trim();
  if (!text) return { ok: true, value: '' };
  if (!/^\d+$/.test(text)) {
    return { ok: false, error: 'Steam AppID 只能包含数字。' };
  }
  return { ok: true, value: text };
}

export function isNumericAppId(value) {
  return /^\d+$/.test(String(value == null ? '' : value).trim());
}

/** 把任意错误安全地转成可展示的一行中文文本，不暴露内部堆栈。 */
export function toDisplayError(error, fallback = '操作未完成，请稍后重试。') {
  if (typeof error === 'string' && error.trim()) return error.trim();
  if (error && typeof error.message === 'string' && error.message.trim()) {
    return error.message.trim();
  }
  return fallback;
}

export function truncateMiddle(value, max = 64) {
  const text = String(value == null ? '' : value);
  if (text.length <= max) return text;
  const edge = Math.floor((max - 1) / 2);
  return `${text.slice(0, edge)}…${text.slice(-edge)}`;
}

export function pluralizeCount(count, unit) {
  return `${formatNumber(count)} ${unit}`;
}
