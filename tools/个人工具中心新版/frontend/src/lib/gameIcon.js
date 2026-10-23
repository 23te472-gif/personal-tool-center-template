/**
 * 游戏图标只接受后端提供的本地 PNG data URL。
 * 不接受 http(s)、file、javascript、SVG 或其他任意 URL。
 */
const PNG_DATA_URL = /^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/;
const MAX_ICON_LENGTH = 4 * 1024 * 1024;

export function getSafeGameIcon(game) {
  const raw = game && typeof game === 'object' ? game.icon : null;
  if (typeof raw !== 'string') return '';
  const icon = raw.trim();
  if (!icon || icon.length > MAX_ICON_LENGTH) return '';
  return PNG_DATA_URL.test(icon) ? icon : '';
}
