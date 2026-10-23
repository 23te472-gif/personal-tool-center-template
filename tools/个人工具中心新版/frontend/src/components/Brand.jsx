export function BrandMark({ size = 36 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="brand-mark"
    >
      <rect width="40" height="40" rx="12" className="brand-mark__base" />
      <rect x="8" y="8" width="15" height="15" rx="4.5" className="brand-mark__mint" />
      <rect x="17" y="17" width="14" height="14" rx="4.5" className="brand-mark__paper" />
      <circle cx="27.5" cy="11.5" r="2.4" className="brand-mark__dot" />
    </svg>
  );
}

export function Brand({ compact = false }) {
  return (
    <div className={`brand ${compact ? 'brand--compact' : ''}`.trim()}>
      <BrandMark size={compact ? 34 : 38} />
      <div className="brand__text">
        <span className="brand__name">个人工具中心</span>
        {!compact ? <span className="brand__caption">Personal Tool Center</span> : null}
      </div>
    </div>
  );
}
