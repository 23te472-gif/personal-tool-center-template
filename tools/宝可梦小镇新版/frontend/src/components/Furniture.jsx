export function FurnitureGlyph({ kind }) {
  if (kind === 'plant') {
    return (
      <g>
        <ellipse cx="20" cy="34" rx="11" ry="3.5" fill="#7d8a6b" opacity=".2" />
        <path d="M13 25h14l-2 11h-10Z" fill="#c58d66" stroke="#966747" strokeWidth="1.2" />
        <path d="M13 25h14l-.6 3.4H13.6Z" fill="#d8a67c" />
        <path d="M20 25c-1-7 2-12 6-14 1 6-1 11-6 14Z" fill="#6f9670" />
        <path d="M20 25c-5-4-7-9-6-14 5 2 8 7 6 14Z" fill="#87aa7f" />
        <path d="M20 25c-1-6-4-9-8-10 1 5 3 9 8 10Z" fill="#9cbb8d" />
        <path d="M20 25c3-5 7-7 11-6-2 5-6 7-11 6Z" fill="#7ea078" />
      </g>
    );
  }
  if (kind === 'rug') {
    return (
      <g>
        <rect x="1" y="6" width="78" height="28" rx="8" fill="#c89e9d" opacity=".5" />
        <rect x="3" y="3" width="74" height="32" rx="8" fill="#e4c8bd" stroke="#b98e87" strokeWidth="1" />
        <rect x="7" y="7" width="66" height="24" rx="5" fill="#f0ded0" />
        {[12, 23, 34, 45, 56, 67].map((x) => (
          <path key={x} d={`M${x} 10l3 6-3 6-3-6Z`} fill="#b78f92" opacity=".8" />
        ))}
        <path d="M7 28h66" stroke="#d8b5a5" strokeWidth="1" />
      </g>
    );
  }
  if (kind === 'bookshelf') {
    return (
      <g>
        <ellipse cx="20" cy="36" rx="13" ry="3" fill="#7d8a6b" opacity=".18" />
        <rect x="6" y="4" width="28" height="33" rx="3" fill="#b88f68" stroke="#8c6848" strokeWidth="1.2" />
        <rect x="9" y="7" width="22" height="27" rx="1.5" fill="#856e56" />
        <path d="M9 17h22M9 27h22" stroke="#c19a72" strokeWidth="2" />
        {[10, 14, 18, 22, 26].map((x, index) => (
          <rect
            key={x}
            x={x}
            y={index % 2 ? 19 : 9}
            width="3.3"
            height={index % 2 ? 7 : 7.5}
            rx=".8"
            fill={['#8fa8a2', '#d1a276', '#b28d8f', '#9eac85', '#7e9a91'][index]}
          />
        ))}
        <rect x="9" y="29" width="22" height="3" fill="#a77e57" />
      </g>
    );
  }
  if (kind === 'bench') {
    return (
      <g>
        <ellipse cx="20" cy="36" rx="15" ry="3" fill="#7d8a6b" opacity=".2" />
        <path d="M8 24h24v4H8z" fill="#a87c58" />
        <path d="M7 14h26v10H7z" fill="#c79b72" stroke="#96704e" strokeWidth="1" />
        <path d="M10 17h20M10 21h20" stroke="#e0b98f" strokeWidth="1.4" />
        <path d="M10 28v6M30 28v6" stroke="#6c7e6d" strokeWidth="2" strokeLinecap="round" />
      </g>
    );
  }
  if (kind === 'flowerbed') {
    return (
      <g>
        <ellipse cx="20" cy="35" rx="15" ry="3" fill="#7d8a6b" opacity=".18" />
        <path d="M4 24h32l-3 10H7Z" fill="#b98c67" stroke="#906c4d" strokeWidth="1" />
        <path d="M7 24h26l-1 4H8Z" fill="#6d644a" />
        {[
          [12, 17, '#dca1a0'],
          [20, 12, '#e8c982'],
          [28, 18, '#bca4c4'],
        ].map(([x, y, color]) => (
          <g key={x}>
            <path d={`M${x} ${y + 2}v9`} stroke="#6f9163" strokeWidth="1.3" />
            {[0, 72, 144, 216, 288].map((angle) => (
              <circle
                key={angle}
                cx={x + Math.cos((angle * Math.PI) / 180) * 3}
                cy={y + Math.sin((angle * Math.PI) / 180) * 3}
                r="2.4"
                fill={color}
              />
            ))}
            <circle cx={x} cy={y} r="1.8" fill="#f2d989" />
          </g>
        ))}
      </g>
    );
  }
  if (kind === 'lamp') {
    return (
      <g>
        <ellipse cx="20" cy="36" rx="9" ry="3" fill="#7d8a6b" opacity=".25" />
        <path d="M20 35V13" stroke="#62796a" strokeWidth="3" strokeLinecap="round" />
        <path d="M13 19h14l-2-11H15Z" fill="#f2d59c" stroke="#7b8b76" strokeWidth="1.2" />
        <path d="M13 19h14" stroke="#6d826f" strokeWidth="2" />
        <circle cx="20" cy="14" r="7" fill="#f7dfa8" opacity=".22" />
        <rect x="16" y="32" width="8" height="3" rx="1.5" fill="#6d826f" />
      </g>
    );
  }
  return (
    <g>
      <rect x="6" y="8" width="28" height="26" rx="3" fill="#c9b48e" stroke="#947c5f" />
      <path d="M6 18h28M6 27h28" stroke="#a38a68" />
    </g>
  );
}

export function FurnitureIcon({ kind, size = 30 }) {
  return (
    <svg
      className="furniture-icon"
      width={size}
      height={size}
      viewBox="0 0 40 40"
      aria-hidden="true"
    >
      <FurnitureGlyph kind={kind} />
    </svg>
  );
}
