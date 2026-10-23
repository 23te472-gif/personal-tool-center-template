import test from 'node:test';
import assert from 'node:assert/strict';
import {
  addDays,
  canPlace,
  cellFromPoint,
  displayReward,
  formatClock,
  isSafePngDataUrl,
  isSnapshot,
  placedLocation,
  taskRows,
  weekTotals,
  weeklySeries,
} from '../src/lib/town.js';
import { normalizeBridgeResponse } from '../src/lib/bridge.js';

const catalog = {
  shop: [
    { id: 'bench', name: '长椅', cost: 4, width: 1, height: 1, description: '坐一会儿' },
    { id: 'rug', name: '地毯', cost: 3, width: 2, height: 1, description: '柔软角落' },
  ],
  partners: [{ id: 'p1', name: '妙蛙种子', image: 'data:image/png;base64,AAAA' }],
  areas: [
    { id: 'home', name: '家园', blocked: [[1, 1]], unlock_cost: 0 },
    { id: 'orchard', name: '果园', blocked: [], unlock_cost: 12 },
  ],
  durations: [5, 15, 25, 45],
  map: { width: 4, height: 3 },
};

const town = {
  version: 1,
  berries: 20,
  areas: ['home'],
  inventory: { a: 'bench', b: 'bench', r: 'rug' },
  placements: { home: { b: [2, 1] }, plaza: {}, orchard: {} },
  partner: 'p1',
  affinity: { p1: 5 },
  daily: {
    '2026-10-23': {
      greeted: ['p1'],
      watered: false,
      arranged: false,
      claimed: ['greet'],
      harvested: false,
    },
  },
  achievements: ['friend'],
  stats: {
    '2026-10-23': { sessions: 2, minutes: 50 },
    '2026-10-22': { sessions: 1, minutes: 25 },
  },
  focus: { task: '读书', duration: 25, remaining: 600, active: true, session_id: 's1' },
  origin: 'new',
};

const snapshot = {
  app: { name: '宝可梦小镇与专注', version: '2.0.0' },
  town,
  focus: { task: '读书', duration: 25, remaining: 600, active: true, running: true, session_id: 's1' },
  catalog,
  today: '2026-10-23',
  settings: { mode: 'town', theme: 'light', motion: true },
  message: '',
};

test('bridge responses normalize success, failure and malformed payloads', () => {
  assert.deepEqual(normalizeBridgeResponse({ ok: true, data: { a: 1 } }), {
    ok: true,
    data: { a: 1 },
    error: null,
  });
  assert.deepEqual(normalizeBridgeResponse({ ok: false, error: ' 保存失败 ' }), {
    ok: false,
    data: null,
    error: '保存失败',
  });
  assert.equal(normalizeBridgeResponse({ ok: false }).ok, false);
  assert.equal(normalizeBridgeResponse(null).ok, false);
  assert.equal(normalizeBridgeResponse({ ok: 'yes' }).ok, false);
});

test('snapshot validation requires the frozen top-level shape', () => {
  assert.equal(isSnapshot(snapshot), true);
  assert.equal(isSnapshot(null), false);
  assert.equal(isSnapshot({ ...snapshot, catalog: {} }), false);
  assert.equal(isSnapshot({ ...snapshot, focus: [] }), false);
});

test('timer and reward display never go negative or invent rewards', () => {
  assert.equal(formatClock(1500), '25:00');
  assert.equal(formatClock(59.2), '01:00');
  assert.equal(formatClock(-2), '00:00');
  assert.equal(displayReward(25), 5);
  assert.equal(displayReward(5), 1);
  assert.equal(displayReward(0), 0);
  assert.equal(displayReward(undefined), 0);
});

test('only local PNG base64 data URLs pass image validation', () => {
  assert.equal(isSafePngDataUrl('data:image/png;base64,AAAA'), true);
  assert.equal(isSafePngDataUrl(''), true);
  assert.equal(isSafePngDataUrl('https://example.com/a.png'), false);
  assert.equal(isSafePngDataUrl('data:image/svg+xml;base64,AAAA'), false);
  assert.equal(isSafePngDataUrl('data:image/png;base64,AA AA'), false);
});

test('coordinate mapping follows the 16x10 grid and rejects outside points', () => {
  const rect = { left: 100, top: 50, width: 640, height: 400 };
  assert.deepEqual(cellFromPoint(100, 50, rect), { x: 0, y: 0 });
  assert.deepEqual(cellFromPoint(739, 449, rect), { x: 15, y: 9 });
  assert.equal(cellFromPoint(740, 450, rect), null);
  assert.equal(cellFromPoint(10, 10, { width: 0, height: 0 }), null);
});

test('furniture collision checks bounds, blocked cells and footprints', () => {
  assert.equal(canPlace({ town, catalog, area: 'home', itemId: 'a', x: 2, y: 1 }).ok, false);
  assert.equal(canPlace({ town, catalog, area: 'home', itemId: 'a', x: 1, y: 1 }).ok, false);
  assert.equal(canPlace({ town, catalog, area: 'home', itemId: 'a', x: 3, y: 1 }).ok, true);
  assert.equal(canPlace({ town, catalog, area: 'home', itemId: 'r', x: 3, y: 0 }).ok, false);
  assert.equal(canPlace({ town, catalog, area: 'home', itemId: 'r', x: 2, y: 0 }).ok, true);
  assert.equal(canPlace({ town, catalog, area: 'orchard', itemId: 'a', x: 0, y: 0 }).ok, false);
  assert.equal(canPlace({ town, catalog, area: 'home', itemId: 'a', x: 2, y: 1, ignoreItemId: 'b' }).ok, true);
  assert.equal(canPlace({ town, catalog, area: 'home', itemId: 'missing', x: 0, y: 0 }).ok, false);
});

test('placed item lookup and task readiness come from snapshot state', () => {
  assert.deepEqual(placedLocation(town, 'b'), { area: 'home', position: [2, 1] });
  assert.equal(placedLocation(town, 'a'), null);
  const rows = taskRows(town, '2026-10-23');
  assert.equal(rows.find((row) => row.id === 'greet').claimed, true);
  assert.equal(rows.find((row) => row.id === 'water').ready, false);
  assert.equal(rows.find((row) => row.id === 'arrange').ready, false);
});

test('weekly series is exactly seven ordered local days and totals only those days', () => {
  assert.equal(addDays('2026-10-23', -1), '2026-10-22');
  assert.equal(addDays('2026-01-01', -1), '2025-12-31');
  const series = weeklySeries(town.stats, '2026-10-23');
  assert.equal(series.length, 7);
  assert.deepEqual(series[6], { day: '2026-10-23', label: '10/23', sessions: 2, minutes: 50 });
  assert.deepEqual(weekTotals(town.stats, '2026-10-23'), { sessions: 3, minutes: 75 });
});
