export const DURATIONS = [5, 15, 25, 45];
export const CELL = 40;
export const TASKS = [
  { id: 'greet', label: '和伙伴打招呼', reward: 2, hint: '在小镇里问候一次伙伴' },
  { id: 'water', label: '照顾庭院树', reward: 3, hint: '给小镇的树浇一点水' },
  { id: 'arrange', label: '布置一件家具', reward: 2, hint: '摆放或移动任意家具' },
];

export function isSafePngDataUrl(value) {
  return (
    value === '' ||
    (typeof value === 'string' &&
      value.length <= 8_000_000 &&
      /^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/.test(value))
  );
}

export function safePartnerImage(partner) {
  return partner && isSafePngDataUrl(partner.image) ? partner.image : '';
}

export function formatClock(totalSeconds) {
  const safe = Math.max(0, Math.ceil(Number(totalSeconds) || 0));
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

export function displayReward(minutes) {
  const value = Number(minutes);
  return Number.isFinite(value) && value > 0 ? Math.floor(value / 5) : 0;
}

function localDateFromIso(iso) {
  const parsed = new Date(`${iso}T12:00:00`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function isoFromDate(date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-');
}

export function addDays(iso, amount) {
  const date = localDateFromIso(iso);
  if (!date) return iso;
  date.setDate(date.getDate() + amount);
  return isoFromDate(date);
}

export function todayDaily(town, today) {
  const value = town && town.daily && town.daily[today];
  return {
    greeted: Array.isArray(value && value.greeted) ? value.greeted : [],
    watered: Boolean(value && value.watered),
    arranged: Boolean(value && value.arranged),
    claimed: Array.isArray(value && value.claimed) ? value.claimed : [],
    harvested: Boolean(value && value.harvested),
  };
}

export function taskRows(town, today) {
  const daily = todayDaily(town, today);
  return TASKS.map((task) => {
    const ready =
      task.id === 'greet'
        ? daily.greeted.length > 0
        : task.id === 'water'
          ? daily.watered
          : daily.arranged;
    const claimed = daily.claimed.includes(task.id);
    return { ...task, ready, claimed, claimable: ready && !claimed, daily };
  });
}

export function areaUnlocked(town, areaId) {
  return Boolean(town && Array.isArray(town.areas) && town.areas.includes(areaId));
}

export function shopEntry(catalog, kind) {
  return (
    (catalog && catalog.shop && catalog.shop.find((entry) => entry.id === kind)) || null
  );
}

export function footprintFor(catalog, kind) {
  const entry = shopEntry(catalog, kind);
  const width = Number(entry && entry.width) || (kind === 'rug' ? 2 : 1);
  const height = Number(entry && entry.height) || 1;
  return { width: Math.max(1, width), height: Math.max(1, height) };
}

export function placementsFor(town, area) {
  return (town && town.placements && town.placements[area]) || {};
}

export function placedLocation(town, itemId) {
  if (!town || !town.placements) return null;
  for (const [area, positions] of Object.entries(town.placements)) {
    if (positions && Object.prototype.hasOwnProperty.call(positions, itemId)) {
      return { area, position: positions[itemId] };
    }
  }
  return null;
}

export function blockedSet(catalog, area) {
  const entry =
    catalog && Array.isArray(catalog.areas)
      ? catalog.areas.find((candidate) => candidate.id === area)
      : null;
  return new Set(
    (entry && Array.isArray(entry.blocked) ? entry.blocked : [])
      .filter((cell) => Array.isArray(cell) && cell.length === 2)
      .map(([x, y]) => `${x},${y}`)
  );
}

export function occupiedSet(town, catalog, area, ignoreItemId = null) {
  const occupied = blockedSet(catalog, area);
  const positions = placementsFor(town, area);
  for (const [itemId, position] of Object.entries(positions)) {
    if (itemId === ignoreItemId || !Array.isArray(position)) continue;
    const kind = town.inventory && town.inventory[itemId];
    const { width, height } = footprintFor(catalog, kind);
    for (let dx = 0; dx < width; dx += 1) {
      for (let dy = 0; dy < height; dy += 1) {
        occupied.add(`${position[0] + dx},${position[1] + dy}`);
      }
    }
  }
  return occupied;
}

export function canPlace({
  town,
  catalog,
  area,
  itemId,
  x,
  y,
  ignoreItemId = null,
}) {
  const map = (catalog && catalog.map) || { width: 16, height: 10 };
  const kind = town && town.inventory ? town.inventory[itemId] : null;
  if (!kind || !shopEntry(catalog, kind)) return { ok: false, reason: '这件家具不在库存里' };
  if (!areaUnlocked(town, area)) return { ok: false, reason: '这个区域还没有开放' };
  if (!Number.isInteger(x) || !Number.isInteger(y)) return { ok: false, reason: '请选择地图上的格子' };
  const { width, height } = footprintFor(catalog, kind);
  if (x < 0 || y < 0 || x + width > map.width || y + height > map.height) {
    return { ok: false, reason: '这里超出地图边界了', width, height };
  }
  const occupied = occupiedSet(town, catalog, area, ignoreItemId);
  for (let dx = 0; dx < width; dx += 1) {
    for (let dy = 0; dy < height; dy += 1) {
      if (occupied.has(`${x + dx},${y + dy}`)) {
        return { ok: false, reason: '这里已经有道路、建筑或家具了', width, height };
      }
    }
  }
  return { ok: true, reason: '', width, height };
}

export function cellFromPoint(clientX, clientY, rect, map = { width: 16, height: 10 }) {
  if (!rect || !rect.width || !rect.height) return null;
  const x = Math.floor(((clientX - rect.left) / rect.width) * map.width);
  const y = Math.floor(((clientY - rect.top) / rect.height) * map.height);
  if (x < 0 || y < 0 || x >= map.width || y >= map.height) return null;
  return { x, y };
}

export function weeklySeries(stats, today) {
  const source = stats && typeof stats === 'object' ? stats : {};
  return Array.from({ length: 7 }, (_, index) => {
    const day = addDays(today, index - 6);
    const value = source[day] || {};
    return {
      day,
      label: day.slice(5).replace('-', '/'),
      sessions: Number(value.sessions) || 0,
      minutes: Number(value.minutes) || 0,
    };
  });
}

export function weekTotals(stats, today) {
  return weeklySeries(stats, today).reduce(
    (sum, day) => ({
      sessions: sum.sessions + day.sessions,
      minutes: sum.minutes + day.minutes,
    }),
    { sessions: 0, minutes: 0 }
  );
}

export function todayStats(town, today) {
  const value = town && town.stats && town.stats[today];
  return {
    sessions: Number(value && value.sessions) || 0,
    minutes: Number(value && value.minutes) || 0,
  };
}

export function partnerName(catalog, partnerId) {
  const partner =
    catalog && Array.isArray(catalog.partners)
      ? catalog.partners.find((candidate) => candidate.id === partnerId)
      : null;
  return partner ? partner.name : '伙伴';
}

export function areaName(catalog, areaId) {
  const area =
    catalog && Array.isArray(catalog.areas)
      ? catalog.areas.find((candidate) => candidate.id === areaId)
      : null;
  return area ? area.name : areaId;
}

export function isSnapshot(value) {
  return Boolean(
    value &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      value.app &&
      typeof value.app === 'object' &&
      !Array.isArray(value.app) &&
      value.town &&
      typeof value.town === 'object' &&
      !Array.isArray(value.town) &&
      value.focus &&
      typeof value.focus === 'object' &&
      !Array.isArray(value.focus) &&
      value.catalog &&
      typeof value.catalog === 'object' &&
      !Array.isArray(value.catalog) &&
      Array.isArray(value.catalog.shop) &&
      Array.isArray(value.catalog.partners) &&
      Array.isArray(value.catalog.areas)
  );
}

export function inventoryEntries(town) {
  if (!town || !town.inventory || typeof town.inventory !== 'object') return [];
  return Object.entries(town.inventory)
    .map(([id, kind]) => {
      const location = placedLocation(town, id);
      return { id, kind, area: location ? location.area : null };
    })
    .sort((a, b) => a.kind.localeCompare(b.kind) || a.id.localeCompare(b.id));
}
