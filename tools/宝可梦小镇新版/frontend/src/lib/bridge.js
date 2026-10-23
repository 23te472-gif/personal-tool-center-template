export const BRIDGE_UNAVAILABLE =
  '还没有连上小镇的本地服务。请从工具中心重新打开，或稍后重试。';
export const BRIDGE_FAILED = '和本地小镇的连接中断了，请重试。';
export const BRIDGE_BAD_RESPONSE = '本地服务返回了无法识别的结果，请重试。';
const FALLBACK_ERROR = '这一步没有完成，请稍后再试。';

export function normalizeBridgeResponse(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    return { ok: false, data: null, error: BRIDGE_BAD_RESPONSE };
  }
  if (raw.ok === true) {
    return { ok: true, data: raw.data === undefined ? null : raw.data, error: null };
  }
  if (raw.ok === false) {
    return {
      ok: false,
      data: null,
      error:
        typeof raw.error === 'string' && raw.error.trim()
          ? raw.error.trim()
          : FALLBACK_ERROR,
    };
  }
  return { ok: false, data: null, error: BRIDGE_BAD_RESPONSE };
}

export function createBridge(win) {
  const getApi = () => {
    const api = win && win.pywebview ? win.pywebview.api : null;
    return api && typeof api.call === 'function' ? api : null;
  };
  return {
    available: () => Boolean(getApi()),
    async call(action, payload = {}) {
      if (typeof action !== 'string' || !action.trim()) {
        return { ok: false, data: null, error: BRIDGE_BAD_RESPONSE };
      }
      const api = getApi();
      if (!api) return { ok: false, data: null, error: BRIDGE_UNAVAILABLE, unavailable: true };
      try {
        const raw = await api.call(action, payload || {});
        return normalizeBridgeResponse(raw);
      } catch {
        return { ok: false, data: null, error: BRIDGE_FAILED, connectionError: true };
      }
    },
  };
}
