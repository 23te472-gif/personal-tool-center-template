import test from 'node:test';
import assert from 'node:assert/strict';
import { getSafeGameIcon } from '../src/lib/gameIcon.js';

test('只接受本地 PNG base64 data URL', () => {
  const icon = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB';
  assert.equal(getSafeGameIcon({ icon }), icon);
  assert.equal(getSafeGameIcon({ icon: `  ${icon}  ` }), icon);
});

test('拒绝外站、非 PNG 与任意 URL', () => {
  for (const icon of [
    'https://example.com/a.png',
    'file:///C:/icon.png',
    'javascript:alert(1)',
    'data:image/svg+xml;base64,PHN2Zz4=',
    'data:image/jpeg;base64,AAAA',
    'data:text/plain;base64,AAAA',
    'data:image/png;base64,',
    'data:image/png,notbase64',
    '',
    null,
    42,
  ]) {
    assert.equal(getSafeGameIcon({ icon }), '');
  }
  assert.equal(getSafeGameIcon(null), '');
});
