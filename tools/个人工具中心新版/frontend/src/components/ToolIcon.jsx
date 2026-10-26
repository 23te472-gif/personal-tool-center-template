import { useEffect, useState } from 'react';
import {
  AppWindow,
  Bot,
  ChartBar,
  FileText,
  Gamepad2,
  House,
  Monitor,
  PackageOpen,
  Palette,
  Presentation,
  Timer,
  Wrench,
} from 'lucide-react';
import { getSafeGameIcon } from '../lib/gameIcon.js';

const TOOL_ICONS = {
  games: Gamepad2,
  delivery: PackageOpen,
  town: House,
  status: Monitor,
  agent: Bot,
  focus: Timer,
  icons: Palette,
};

const TOOL_TONES = {
  games: 'blue',
  delivery: 'mint',
  town: 'amber',
  status: 'slate',
  agent: 'mint',
  focus: 'rose',
  icons: 'teal',
};

export function ToolIcon({ id, size = 22 }) {
  const Icon = TOOL_ICONS[id] || AppWindow;
  return <Icon size={size} aria-hidden="true" />;
}

export function toolTone(id) {
  return TOOL_TONES[id] || 'slate';
}

const MATERIAL_ICONS = {
  thesis: FileText,
  presentation: Presentation,
  charts: ChartBar,
};

export function MaterialIcon({ id, size = 20 }) {
  const Icon = MATERIAL_ICONS[id] || FileText;
  return <Icon size={size} aria-hidden="true" />;
}

export function initialsForGame(game) {
  const name = String((game && (game.name || game.english_name)) || '').trim();
  if (!name) return '游';
  if (/[\u3400-\u9fff]/.test(name)) return name.slice(0, 2);
  const words = name.split(/\s+/).filter(Boolean);
  if (words.length >= 2) return `${words[0][0]}${words[1][0]}`.toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

export function gameTone(game) {
  const source = String((game && (game.id || game.name || game.english_name)) || 'game');
  let hash = 0;
  for (let index = 0; index < source.length; index += 1) {
    hash = (hash * 31 + source.charCodeAt(index)) % 9973;
  }
  return hash % 6;
}

export function GameAvatar({ game, size = 'md' }) {
  const icon = getSafeGameIcon(game);
  const [failedIcon, setFailedIcon] = useState('');

  useEffect(() => {
    setFailedIcon('');
  }, [icon]);

  const showImage = Boolean(icon) && failedIcon !== icon;

  return (
    <div
      className={`game-avatar game-avatar--${size} game-tone-${gameTone(game)}`}
      aria-hidden="true"
    >
      {showImage ? (
        <img
          className="game-avatar__image"
          src={icon}
          alt=""
          loading="lazy"
          onError={() => setFailedIcon(icon)}
        />
      ) : (
        <span>{initialsForGame(game)}</span>
      )}
      <Wrench size={size === 'lg' ? 13 : 11} className="game-avatar__badge" />
    </div>
  );
}
