import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ value, children }) {
  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    return { notify: () => {} };
  }
  return context;
}

let nextToastId = 1;

const TONES = {
  success: { icon: CheckCircle2, label: '成功' },
  error: { icon: AlertTriangle, label: '错误' },
  info: { icon: Info, label: '提示' },
};

/**
 * 轻量通知。只有 bridge 明确返回 ok:true 后，调用方才应推送 success；
 * 这个组件本身不伪造任何成功文案。
 */
export function useToastStore() {
  const [toasts, setToasts] = useState([]);
  const timers = useRef(new Map());

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const notify = useCallback(
    ({ tone = 'info', title, message, duration } = {}) => {
      const id = nextToastId++;
      const resolvedTone = TONES[tone] ? tone : 'info';
      const toast = {
        id,
        tone: resolvedTone,
        title: title || TONES[resolvedTone].label,
        message: String(message || ''),
      };
      setToasts((current) => [...current.slice(-4), toast]);
      const timeout = Number.isFinite(duration)
        ? duration
        : resolvedTone === 'error'
          ? 9000
          : 4800;
      if (timeout > 0) {
        const timer = setTimeout(() => dismiss(id), timeout);
        timers.current.set(id, timer);
      }
      return id;
    },
    [dismiss]
  );

  useEffect(
    () => () => {
      for (const timer of timers.current.values()) clearTimeout(timer);
      timers.current.clear();
    },
    []
  );

  return useMemo(() => ({ toasts, notify, dismiss }), [toasts, notify, dismiss]);
}

export function ToastViewport({ toasts, onDismiss }) {
  return (
    <div className="toast-viewport" aria-live="polite" aria-atomic="false">
      {toasts.map((toast) => {
        const ToneIcon = TONES[toast.tone].icon;
        return (
          <div key={toast.id} className={`toast toast--${toast.tone}`} role="status">
            <div className="toast__icon" aria-hidden="true">
              <ToneIcon size={18} />
            </div>
            <div className="toast__content">
              <strong>{toast.title}</strong>
              {toast.message ? <p>{toast.message}</p> : null}
            </div>
            <button type="button" className="toast__close" onClick={() => onDismiss(toast.id)} aria-label="关闭通知">
              <X size={15} aria-hidden="true" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
