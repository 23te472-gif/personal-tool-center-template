import test from 'node:test';
import assert from 'node:assert/strict';
import { millisecondsUntilJapanMidnight } from '../src/lib/lifecycle.js';

test('daily refresh is scheduled at Tokyo midnight, independently of host timezone',()=>{
  assert.equal(millisecondsUntilJapanMidnight(Date.parse('2026-10-23T14:59:59Z')),1150);
  assert.equal(millisecondsUntilJapanMidnight(Date.parse('2026-10-23T15:00:00Z')),86400150);
  assert.equal(millisecondsUntilJapanMidnight(Date.parse('2026-10-23T14:59:59.999Z')),151);
});
