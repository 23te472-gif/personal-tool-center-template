import { useMemo } from 'react';
import { safePartnerImage } from '../lib/town.js';
import { FurnitureGlyph } from './Furniture.jsx';

function Window() {
  return (
    <g>
      <rect x="54" y="68" width="174" height="142" rx="14" fill="#fbf4e6" stroke="#c7ab84" strokeWidth="5" />
      <rect x="66" y="80" width="150" height="118" rx="7" fill="#cfe2df" />
      <circle cx="174" cy="112" r="21" fill="#f4d391" opacity=".9" />
      <path d="M66 170c31-29 57-25 78-3 19-23 44-30 72-10v41H66Z" fill="#9fbb9a" />
      <path d="M66 181c36-15 71-10 150 5v12H66Z" fill="#7f9f82" />
      <path d="M140 80v118M66 139h150" stroke="#fbf4e6" strokeWidth="7" />
    </g>
  );
}

export function FocusRoom({ partner, inventory, motion, hidden }) {
  const image = safePartnerImage(partner);
  const names = partner ? partner.name : '伙伴';
  const kinds = useMemo(() => new Set(Object.values(inventory || {})), [inventory]);
  const hasRug = kinds.has('rug');
  const hasPlant = kinds.has('plant');
  const hasShelf = kinds.has('bookshelf');

  return (
    <div className={`focus-room ${motion && !hidden ? 'is-alive' : ''}`.trim()}>
      <svg viewBox="0 0 720 480" className="focus-room__svg" role="img" aria-label={`${names}在安静的小屋里陪你专注`}>
        <defs>
          <linearGradient id="wallWash" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#f8eedf" />
            <stop offset="1" stopColor="#efe2cf" />
          </linearGradient>
          <linearGradient id="floorWood" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#d8b996" />
            <stop offset="1" stopColor="#c8a47e" />
          </linearGradient>
          <filter id="roomShadow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="7" stdDeviation="7" floodColor="#7a6149" floodOpacity=".14" />
          </filter>
        </defs>
        <rect width="720" height="480" fill="url(#wallWash)" />
        <path d="M0 332h720v148H0Z" fill="url(#floorWood)" />
        <path d="M0 348h720M0 382h720M0 422h720M0 463h720" stroke="#b9936f" strokeWidth="2" opacity=".38" />
        <path d="M120 332v148M415 332v148M612 332v148" stroke="#b9936f" strokeWidth="1.5" opacity=".28" />
        <path d="M0 330h720" stroke="#b28f6c" strokeWidth="8" />
        <path d="M0 345h720" stroke="#fff4e1" strokeWidth="2" opacity=".55" />
        <Window />
        <g opacity=".9">
          <path d="M594 78h50v86h-50z" fill="#c3a27d" />
          <path d="M599 84h40v74h-40z" fill="#ead7b9" />
          <path d="M604 95h30M604 120h30M604 145h30" stroke="#c7ab88" strokeWidth="3" />
          <circle cx="619" cy="72" r="14" fill="#d4b78f" />
          <circle cx="619" cy="72" r="8" fill="#f1e0c4" />
        </g>
        <g opacity=".8">
          <ellipse cx="360" cy="308" rx="190" ry="31" fill="#8d7358" opacity=".14" />
          <path d="M270 320h187l-18 26H286Z" fill="#bf9a76" opacity=".55" />
        </g>
        {hasRug && (
          <g transform="translate(205 380) scale(3.85 1.55)" filter="url(#roomShadow)">
            <FurnitureGlyph kind="rug" />
          </g>
        )}
        {hasShelf && (
          <g transform="translate(552 213) scale(2.5)" filter="url(#roomShadow)">
            <FurnitureGlyph kind="bookshelf" />
          </g>
        )}
        {hasPlant && (
          <g transform="translate(628 330) scale(2.15)" filter="url(#roomShadow)">
            <FurnitureGlyph kind="plant" />
          </g>
        )}
        <g transform="translate(356 310)" className="room-partner">
          <ellipse cx="0" cy="34" rx="60" ry="13" fill="#8b735b" opacity=".2" />
          <g className="room-partner__bob">
            {image ? (
              <image href={image} x="-76" y="-106" width="152" height="152" preserveAspectRatio="xMidYMax meet" />
            ) : (
              <circle cx="0" cy="-18" r="48" fill="#f4f1df" stroke="#b2c0a5" strokeWidth="2" />
            )}
          </g>
          <path d="M-28 -113c4-17 14-27 28-27s25 10 29 27" fill="none" stroke="#9bb096" strokeWidth="3" opacity=".35" />
        </g>
        <g className="room-lamp">
          <path d="M666 330V204" stroke="#6d816f" strokeWidth="4" strokeLinecap="round" />
          <path d="M644 213h45l-8-30h-29Z" fill="#f0d499" stroke="#7d8f7a" strokeWidth="2" />
          <ellipse cx="666" cy="206" rx="34" ry="12" fill="#f6e1af" opacity=".18" />
        </g>
        <g opacity=".65">
          <circle cx="105" cy="286" r="4" fill="#d6aa9c" />
          <circle cx="126" cy="296" r="2.5" fill="#d6aa9c" />
          <circle cx="89" cy="302" r="2" fill="#d6aa9c" />
        </g>
        <rect x="0" y="470" width="720" height="10" fill="#a8815d" opacity=".35" />
      </svg>
      <div className="focus-room__caption">
        <span className="focus-room__dot" aria-hidden="true" />
        {motion && !hidden ? '小屋里有轻轻的呼吸声' : '小屋安静地陪着你'}
      </div>
    </div>
  );
}
