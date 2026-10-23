/** 全局搜索与游戏筛选的纯函数，供界面与测试共用。 */

import { normalizeText } from './format.js';

export const TOOL_CATEGORY_LABELS = {
  game: '游戏',
  work: '效率',
  fun: '趣味',
  system: '系统',
};

export const MATERIAL_LABELS = {
  thesis: '论文资料',
  presentation: '演示文稿',
  charts: '图表资料',
};

export const SEARCH_TYPE_LABELS = {
  tool: '工具',
  game: '游戏',
  material: '资料',
  wheel: '转盘',
};

const TYPE_ORDER = { tool: 0, game: 1, material: 2, wheel: 3 };

export function tokenizeQuery(query) {
  const normalized = normalizeText(query);
  return normalized ? normalized.split(' ').filter(Boolean) : [];
}

function fieldMatchScore(rawValue, term, weight) {
  const value = normalizeText(rawValue);
  if (!value || !term) return 0;
  if (!value.includes(term)) return 0;
  if (value === term) return weight + 100;
  if (value.startsWith(term)) return weight + 40;
  return weight;
}

const GAME_FIELDS = [
  { key: 'name', weight: 10 },
  { key: 'english_name', weight: 8 },
  { key: 'aliases', weight: 6 },
  { key: 'notes', weight: 2 },
];

function gameFieldValues(game, key) {
  if (key === 'aliases') {
    return Array.isArray(game.aliases) ? game.aliases : [];
  }
  return [game[key]];
}

export function gameMatchesQuery(game, query) {
  const terms = tokenizeQuery(query);
  if (!terms.length) return true;
  if (!game) return false;
  const values = [];
  for (const field of GAME_FIELDS) {
    values.push(...gameFieldValues(game, field.key));
  }
  const haystack = normalizeText(values.join(' '));
  return terms.every((term) => haystack.includes(term));
}

export function scoreGame(game, query) {
  const terms = tokenizeQuery(query);
  if (!game) return 0;
  if (!terms.length) return 1;
  let total = 0;
  for (const term of terms) {
    let best = 0;
    for (const field of GAME_FIELDS) {
      for (const value of gameFieldValues(game, field.key)) {
        best = Math.max(best, fieldMatchScore(value, term, field.weight));
      }
    }
    if (!best) return 0;
    total += best;
  }
  return total;
}

export function filterGames(games, query, options = {}) {
  const list = Array.isArray(games) ? games : [];
  const favoritesOnly = Boolean(options.favoritesOnly);
  return list.filter((game) => {
    if (favoritesOnly && !game.favorite) return false;
    return gameMatchesQuery(game, query);
  });
}

function scoreTool(tool, query) {
  const terms = tokenizeQuery(query);
  if (!terms.length) return 1;
  const fields = [
    { value: tool.name, weight: 10 },
    { value: tool.id, weight: 4 },
    { value: tool.description, weight: 4 },
    { value: TOOL_CATEGORY_LABELS[tool.category], weight: 1 },
  ];
  let total = 0;
  for (const term of terms) {
    let best = 0;
    for (const field of fields) {
      best = Math.max(best, fieldMatchScore(field.value, term, field.weight));
    }
    if (!best) return 0;
    total += best;
  }
  return total;
}

function scoreMaterial(material, query) {
  const terms = tokenizeQuery(query);
  if (!terms.length) return 1;
  const fields = [
    { value: material.title, weight: 10 },
    { value: material.name, weight: 6 },
    { value: material.path, weight: 2 },
    { value: MATERIAL_LABELS[material.id], weight: 5 },
  ];
  let total = 0;
  for (const term of terms) {
    let best = 0;
    for (const field of fields) {
      best = Math.max(best, fieldMatchScore(field.value, term, field.weight));
    }
    if (!best) return 0;
    total += best;
  }
  return total;
}

function scoreWheelEntry(entry, query) {
  const terms = tokenizeQuery(query);
  if (!terms.length) return 1;
  const fields = [
    { value: entry.name, weight: 10 },
    { value: entry.appid, weight: 3 },
  ];
  let total = 0;
  for (const term of terms) {
    let best = 0;
    for (const field of fields) {
      best = Math.max(best, fieldMatchScore(field.value, term, field.weight));
    }
    if (!best) return 0;
    total += best;
  }
  return total;
}

function materialList(materials) {
  if (!materials || typeof materials !== 'object' || Array.isArray(materials)) return [];
  return Object.entries(materials)
    .filter(([, material]) => material && typeof material === 'object')
    .map(([key, material]) => ({
      ...material,
      id: material.id || key,
      key,
    }));
}

function wheelEntryList(wheel) {
  if (!wheel || !Array.isArray(wheel.entries)) return [];
  return wheel.entries.filter((entry) => entry && typeof entry === 'object');
}

/**
 * 跨工具、游戏、资料、转盘候选的统一检索。
 * data 接受 bootstrap 快照；只读，不触发任何后台动作。
 */
export function searchAll(query, data = {}, limit = 12) {
  if (!tokenizeQuery(query).length) return [];
  const source = data && typeof data === 'object' && !Array.isArray(data) ? data : {};
  const results = [];

  const tools = Array.isArray(source.tools) ? source.tools : [];
  for (const tool of tools) {
    const score = scoreTool(tool, query);
    if (!score) continue;
    results.push({
      type: 'tool',
      id: tool.id,
      title: tool.name || tool.id,
      subtitle: tool.description || TOOL_CATEGORY_LABELS[tool.category] || '本地工具',
      score,
    });
  }

  const games = Array.isArray(source.games) ? source.games : [];
  for (const game of games) {
    const score = scoreGame(game, query);
    if (!score) continue;
    const aliasText = Array.isArray(game.aliases) ? game.aliases.join('、') : '';
    results.push({
      type: 'game',
      id: game.id,
      title: game.name || game.english_name || '未命名游戏',
      subtitle: [game.english_name, aliasText].filter(Boolean).join(' · ') || '游戏管家',
      score,
    });
  }

  for (const material of materialList(source.materials)) {
    const score = scoreMaterial(material, query);
    if (!score) continue;
    results.push({
      type: 'material',
      id: material.key || material.id,
      title: material.title || MATERIAL_LABELS[material.key] || '资料',
      subtitle: material.path || '尚未配置路径',
      score,
    });
  }

  for (const entry of wheelEntryList(source.wheel)) {
    const score = scoreWheelEntry(entry, query);
    if (!score) continue;
    results.push({
      type: 'wheel',
      id: entry.id,
      title: entry.name || '未命名候选',
      subtitle: entry.appid ? `Steam AppID ${entry.appid}` : '自定义候选',
      score,
    });
  }

  results.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    const typeDelta = (TYPE_ORDER[a.type] ?? 9) - (TYPE_ORDER[b.type] ?? 9);
    if (typeDelta !== 0) return typeDelta;
    return String(a.title).localeCompare(String(b.title), 'zh-CN');
  });

  const max = Number.isFinite(limit) && limit > 0 ? Math.floor(limit) : 12;
  return results.slice(0, max);
}
