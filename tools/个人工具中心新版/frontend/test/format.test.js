import test from 'node:test';
import assert from 'node:assert/strict';
import {
  aliasesToText,
  formatBytes,
  isNumericAppId,
  normalizeSteamAppId,
  normalizeText,
  parseAliases,
  toDisplayError,
  truncateMiddle,
} from '../src/lib/format.js';

test('字节格式化覆盖空值、常见单位与非法值', () => {
  assert.equal(formatBytes(0), '0 B');
  assert.equal(formatBytes(null), '0 B');
  assert.equal(formatBytes(Number.NaN), '0 B');
  assert.equal(formatBytes(1024), '1 KB');
  assert.equal(formatBytes(1536), '1.5 KB');
  assert.equal(formatBytes(1024 * 1024), '1 MB');
  assert.equal(formatBytes(1024 ** 3), '1 GB');
});

test('别名按中英文标点和换行拆分、去空并忽略大小写去重', () => {
  assert.deepEqual(parseAliases('星露谷, SDV，sdv; 谷子\n\n'), ['星露谷', 'SDV', '谷子']);
  assert.deepEqual(parseAliases('ＳＤＶ，sdv'), ['ＳＤＶ']);
  assert.deepEqual(parseAliases(''), []);
  assert.deepEqual(parseAliases(null), []);
  assert.equal(aliasesToText(['A', 'B']), 'A、B');
  assert.equal(aliasesToText(null), '');
});

test('Steam AppID 只接受数字', () => {
  assert.deepEqual(normalizeSteamAppId(' 413150 '), { ok: true, value: '413150' });
  assert.deepEqual(normalizeSteamAppId(''), { ok: true, value: '' });
  assert.equal(normalizeSteamAppId('41a').ok, false);
  assert.equal(normalizeSteamAppId('-1').ok, false);
  assert.equal(normalizeSteamAppId('1.5').ok, false);
  assert.equal(isNumericAppId('413150'), true);
  assert.equal(isNumericAppId(''), false);
  assert.equal(isNumericAppId(null), false);
});

test('文本归一化处理全角、空白与大小写', () => {
  assert.equal(normalizeText('  Ｓｔａｒｄｅｗ   Valley  '), 'stardew valley');
  assert.equal(normalizeText(null), '');
  assert.equal(normalizeText(42), '42');
});

test('中间截断只处理超长文本', () => {
  assert.equal(truncateMiddle('short', 10), 'short');
  const long = 'C:\\very\\long\\path\\to\\some\\file\\name.txt';
  const shortened = truncateMiddle(long, 20);
  assert.ok(shortened.length <= 20);
  assert.ok(shortened.includes('…'));
});

test('错误展示不泄露对象内部内容', () => {
  assert.equal(toDisplayError('  中文错误  '), '中文错误');
  assert.equal(toDisplayError(new Error('安全文案')), '安全文案');
  assert.equal(toDisplayError(null), '操作未完成，请稍后重试。');
  assert.equal(toDisplayError({ stack: 'secret' }, '回退'), '回退');
});
