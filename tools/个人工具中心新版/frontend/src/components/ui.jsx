import { Loader2 } from 'lucide-react';

export function Spinner({ size = 16, label = '加载中' }) {
  return (
    <Loader2
      className="spinner"
      width={size}
      height={size}
      strokeWidth={2.2}
      aria-label={label}
      role="img"
    />
  );
}

export function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  icon: Icon,
  children,
  className = '',
  disabled = false,
  type = 'button',
  ...rest
}) {
  const classes = ['btn', `btn--${variant}`, `btn--${size}`, className]
    .filter(Boolean)
    .join(' ');
  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner size={size === 'sm' ? 14 : 16} /> : Icon ? <Icon size={size === 'sm' ? 15 : 17} aria-hidden="true" /> : null}
      {children ? <span>{children}</span> : null}
    </button>
  );
}

export function IconButton({ label, icon: Icon, size = 18, className = '', variant = 'ghost', ...rest }) {
  return (
    <button
      type="button"
      className={`icon-btn icon-btn--${variant} ${className}`.trim()}
      aria-label={label}
      title={label}
      {...rest}
    >
      <Icon size={size} aria-hidden="true" />
    </button>
  );
}

export function Badge({ tone = 'neutral', children, dot = false, className = '' }) {
  return (
    <span className={`badge badge--${tone} ${className}`.trim()}>
      {dot ? <span className="badge__dot" aria-hidden="true" /> : null}
      {children}
    </span>
  );
}

export function PageHeader({ eyebrow, title, description, actions, children }) {
  return (
    <header className="page-header">
      <div className="page-header__text">
        {eyebrow ? <div className="eyebrow">{eyebrow}</div> : null}
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
        {children}
      </div>
      {actions ? <div className="page-header__actions">{actions}</div> : null}
    </header>
  );
}

export function SectionHeader({ title, description, action, id }) {
  return (
    <div className="section-header">
      <div>
        <h2 id={id}>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {action ? <div className="section-header__action">{action}</div> : null}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action, compact = false }) {
  return (
    <div className={`empty-state ${compact ? 'empty-state--compact' : ''}`.trim()}>
      {Icon ? (
        <div className="empty-state__icon" aria-hidden="true">
          <Icon size={compact ? 22 : 28} />
        </div>
      ) : null}
      <div className="empty-state__body">
        <h3>{title}</h3>
        {description ? <p>{description}</p> : null}
      </div>
      {action ? <div className="empty-state__action">{action}</div> : null}
    </div>
  );
}

export function InlineAlert({ tone = 'error', title, children, action, onDismiss }) {
  return (
    <div className={`inline-alert inline-alert--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <div className="inline-alert__body">
        {title ? <strong>{title}</strong> : null}
        {children ? <div className="inline-alert__text">{children}</div> : null}
      </div>
      {action ? <div className="inline-alert__action">{action}</div> : null}
      {onDismiss ? (
        <button type="button" className="inline-alert__close" onClick={onDismiss} aria-label="关闭提示">
          ×
        </button>
      ) : null}
    </div>
  );
}

export function Field({ label, htmlFor, hint, error, required, children, className = '' }) {
  return (
    <div className={`field ${error ? 'field--error' : ''} ${className}`.trim()}>
      <label htmlFor={htmlFor}>
        {label}
        {required ? <span className="field__required" aria-hidden="true"> *</span> : null}
      </label>
      {children}
      {error ? <p className="field__error" role="alert">{error}</p> : hint ? <p className="field__hint">{hint}</p> : null}
    </div>
  );
}

export function Switch({ checked, onChange, label, description, disabled = false, id }) {
  return (
    <label className={`switch-row ${disabled ? 'is-disabled' : ''}`.trim()} htmlFor={id}>
      <span className="switch-row__text">
        <span className="switch-row__label">{label}</span>
        {description ? <span className="switch-row__description">{description}</span> : null}
      </span>
      <span className="switch">
        <input
          id={id}
          type="checkbox"
          role="switch"
          checked={Boolean(checked)}
          onChange={(event) => onChange(event.target.checked)}
          disabled={disabled}
        />
        <span className="switch__track" aria-hidden="true">
          <span className="switch__thumb" />
        </span>
      </span>
    </label>
  );
}

export function Kbd({ children }) {
  return <kbd className="kbd">{children}</kbd>;
}
