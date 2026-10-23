/**
 * pywebview bridge 的薄封装。
 *
 * 契约：window.pywebview.api.call(action, payload) 返回
 *   { ok: true, data: ... } 或 { ok: false, error: '中文错误' }
 * Promise reject 视为连接失败。桥未就绪时绝不返回成功。
 */

export const BRIDGE_UNAVAILABLE =
  '本地桌面服务尚未就绪。请确认应用窗口已完全打开，然后重试。';
export const BRIDGE_CALL_FAILED =
  '与本地桌面服务的连接已中断。请稍候重试；若持续失败，可重新打开应用。';
export const BRIDGE_BAD_RESPONSE =
  '本地服务返回了无法识别的结果，请重试。';

const FALLBACK_ERROR = '操作未完成，请稍后重试。';

export function getRawBridge(win) {
  const api = win && win.pywebview ? win.pywebview.api : null;
  return api && typeof api.call === 'function' ? api : null;
}

/** 把 bridge 返回值规整为统一的 {ok,data,error}，任何异常形状都按失败处理。 */
export function normalizeBridgeResponse(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    return { ok: false, data: null, error: BRIDGE_BAD_RESPONSE };
  }

  if (raw.ok === true) {
    return { ok: true, data: raw.data === undefined ? null : raw.data, error: null };
  }

  if (raw.ok === false) {
    const message =
      typeof raw.error === 'string' && raw.error.trim()
        ? raw.error.trim()
        : FALLBACK_ERROR;
    return { ok: false, data: null, error: message };
  }

  return { ok: false, data: null, error: BRIDGE_BAD_RESPONSE };
}

/**
 * 创建可注入 window 的 bridge。每次 call 都重新读取 api，
 * 这样 pywebviewready 事件之后才出现的桥也能被使用。
 */
export function createBridge(win) {
  return {
    isAvailable() {
      return Boolean(getRawBridge(win));
    },
    async call(action, payload) {
      if (typeof action !== 'string' || !action.trim()) {
        return { ok: false, data: null, error: BRIDGE_BAD_RESPONSE };
      }

      const api = getRawBridge(win);
      if (!api) {
        return {
          ok: false,
          data: null,
          error: BRIDGE_UNAVAILABLE,
          unavailable: true,
        };
      }

      try {
        const raw = await api.call(action, payload || {});
        return normalizeBridgeResponse(raw);
      } catch {
        return {
          ok: false,
          data: null,
          error: BRIDGE_CALL_FAILED,
          connectionError: true,
        };
      }
    },
  };
}

/** 原生选择器返回 cancelled:true 时属于正常取消，不应当作错误展示。 */
export function isCancellation(result) {
  return Boolean(
    result && result.ok === true && result.data && result.data.cancelled === true
  );
}
