import { safePartnerImage } from '../lib/town.js';

export function PartnerAvatar({ partner, size = 64, className = '' }) {
  const image = safePartnerImage(partner);
  const label = (partner && partner.name) || '伙伴';
  const initial = label.slice(-2) || '伴';
  return (
    <span
      className={`partner-avatar ${className}`.trim()}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      {image ? (
        <img src={image} alt="" draggable="false" loading="lazy" decoding="async" />
      ) : (
        <span className="partner-avatar__fallback">{initial}</span>
      )}
    </span>
  );
}
