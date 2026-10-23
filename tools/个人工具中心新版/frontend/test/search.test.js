import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  filterGames,
  gameMatchesQuery,
  scoreGame,
  searchAll,
  tokenizeQuery,
} from '../src/lib/search.js';

const fixture = JSON.parse(
  readFileSync(new URL('./fixtures/bootstrap.json', import.meta.url), 'utf8')
);
const games = fixture.games;

test('fixture 与 bootstrap 核心字段保持一致', () => {
  assert.ok(fixture.app && fixture.app.name);
  assert.ok(Array.isArray(fixture.tools));
  assert.ok(Array.isArray(fixture.games));
  assert.ok(fixture.materials.thesis);
  assert.ok(Array.isArray(fixture.wheel.entries));
  assert.ok(Array.isArray(fixture.jobs));
});

test('游戏中文名、英文名与别名都可匹配', () => {
  const stardew = games.find((game) => game.id === 'game-stardew');
  assert.equal(gameMatchesQuery(stardew, '星露'), true);
  assert.equal(gameMatchesQuery(stardew, 'stardew'), true);
  assert.equal(gameMatchesQuery(stardew, 'STARDEW'), true);
  assert.equal(gameMatchesQuery(stardew, 'sdv'), true);
  assert.equal(gameMatchesQuery(stardew, '星露谷'), true);
  assert.equal(gameMatchesQuery(stardew, '老头环'), false);
});

test('全角字符与多词查询按 NFKC 归一化处理', () => {
  const stardew = games.find((game) => game.id === 'game-stardew');
  assert.equal(gameMatchesQuery(stardew, 'ＳＤＶ'), true);
  assert.equal(gameMatchesQuery(stardew, '星露  valley'), true);
  assert.equal(gameMatchesQuery(stardew, '星露  hades'), false);
  assert.deepEqual(tokenizeQuery('  Stardew   Valley '), ['stardew', 'valley']);
});

test('备注参与搜索，精确名称得分更高', () => {
  const elden = games.find((game) => game.id === 'game-elden');
  assert.equal(gameMatchesQuery(elden, '开放世界'), true);
  const exact = scoreGame(elden, '艾尔登法环');
  const partial = scoreGame(elden, '艾尔');
  assert.ok(exact > partial);
});

test('收藏筛选与关键词可以叠加', () => {
  assert.equal(filterGames(games, '', { favoritesOnly: true }).length, 2);
  assert.equal(filterGames(games, '哈', { favoritesOnly: true }).length, 1);
  assert.equal(
    filterGames(games, '哈迪斯', { favoritesOnly: false }).some((game) => game.id === 'game-hades'),
    true
  );
});

test('全局搜索覆盖工具、游戏、资料与转盘候选', () => {
  const toolResults = searchAll('打包', fixture);
  assert.ok(toolResults.some((item) => item.type === 'tool' && item.id === 'delivery'));

  const gameResults = searchAll('星露', fixture);
  assert.ok(gameResults.some((item) => item.type === 'game' && item.id === 'game-stardew'));
  assert.ok(gameResults.some((item) => item.type === 'wheel' && item.id === 'wheel-stardew'));
  assert.equal(gameResults[0].type, 'game');

  const materialResults = searchAll('论文', fixture);
  assert.ok(materialResults.some((item) => item.type === 'material' && item.id === 'thesis'));

  const wheelResults = searchAll('随便', fixture);
  assert.ok(wheelResults.some((item) => item.type === 'wheel' && item.id === 'wheel-custom'));
});

test('搜索排序、数量上限与空输入', () => {
  assert.deepEqual(searchAll('', fixture), []);
  assert.deepEqual(searchAll('   ', fixture), []);
  const limited = searchAll('a', fixture, 2);
  assert.ok(limited.length <= 2);
  const all = searchAll('a', fixture, 50);
  assert.ok(all.length >= 2);
  for (let index = 1; index < all.length; index += 1) {
    assert.ok(all[index - 1].score >= all[index].score);
  }
});

test('搜索对缺失或异常数据结构保持安全', () => {
  assert.deepEqual(searchAll('x', null), []);
  assert.deepEqual(searchAll('x', { tools: null, games: 'bad', materials: [] }), []);
  assert.equal(gameMatchesQuery(null, 'x'), false);
  assert.equal(gameMatchesQuery({ name: 'X' }, ''), true);
});
