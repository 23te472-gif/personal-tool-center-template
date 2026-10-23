import test from 'node:test';
import assert from 'node:assert/strict';
import {
  BRIDGE_BAD_RESPONSE,
  BRIDGE_CALL_FAILED,
  BRIDGE_UNAVAILABLE,
  createBridge,
  isCancellation,
  normalizeBridgeResponse,
} from '../src/lib/bridge.js';

test('成功响应保留 data；缺少 data 时为 null', () => {
  assert.deepEqual(normalizeBridgeResponse({ ok: true, data: { value: 1 } }), {
    ok: true,
    data: { value: 1 },
    error: null,
  });
  assert.deepEqual(normalizeBridgeResponse({ ok: true }), {
    ok: true,
    data: null,
    error: null,
  });
});

test('失败响应保留中文错误，不返回 data', () => {
  assert.deepEqual(normalizeBridgeResponse({ ok: false, error: '  文件不存在  ' }), {
    ok: false,
    data: null,
    error: '文件不存在',
  });
  assert.equal(normalizeBridgeResponse({ ok: false, error: '   ' }).error.length > 0, true);
  assert.equal(normalizeBridgeResponse({ ok: false }).ok, false);
});

test('非法响应一律按失败处理，绝不伪装成功', () => {
  for (const value of [null, undefined, 'ok', 42, [], {}, { ok: 'true', data: 1 }]) {
    const result = normalizeBridgeResponse(value);
    assert.equal(result.ok, false);
    assert.equal(result.data, null);
    assert.equal(result.error, BRIDGE_BAD_RESPONSE);
  }
});

test('bridge 会传递 action 与 payload，并支持桥延迟出现', async () => {
  const calls = [];
  const win = {};
  const bridge = createBridge(win);
  assert.equal(bridge.isAvailable(), false);
  const unavailable = await bridge.call('bootstrap', {});
  assert.equal(unavailable.ok, false);
  assert.equal(unavailable.error, BRIDGE_UNAVAILABLE);

  win.pywebview = {
    api: {
      call: async (action, payload) => {
        calls.push({ action, payload });
        return { ok: true, data: { echo: action } };
      },
    },
  };
  assert.equal(bridge.isAvailable(), true);
  const result = await bridge.call('bootstrap', { a: 1 });
  assert.equal(result.ok, true);
  assert.deepEqual(result.data, { echo: 'bootstrap' });
  assert.deepEqual(calls, [{ action: 'bootstrap', payload: { a: 1 } }]);
});

test('bridge 失败响应与 Promise 拒绝都不报告成功', async () => {
  const failing = createBridge({
    pywebview: {
      api: {
        call: async () => ({ ok: false, error: '打包失败' }),
      },
    },
  });
  const failed = await failing.call('pack_start', {});
  assert.equal(failed.ok, false);
  assert.equal(failed.error, '打包失败');
  assert.equal(failed.data, null);

  const rejecting = createBridge({
    pywebview: {
      api: {
        call: async () => {
          throw new Error('internal stack');
        },
      },
    },
  });
  const rejected = await rejecting.call('bootstrap', {});
  assert.equal(rejected.ok, false);
  assert.equal(rejected.error, BRIDGE_CALL_FAILED);
  assert.equal(rejected.connectionError, true);
  assert.equal(rejected.error.includes('internal stack'), false);
});

test('空 action 被拒绝，调用参数默认是对象', async () => {
  let received = null;
  const bridge = createBridge({
    pywebview: {
      api: {
        call: async (_action, payload) => {
          received = payload;
          return { ok: true, data: {} };
        },
      },
    },
  });
  assert.equal((await bridge.call('', {})).ok, false);
  await bridge.call('game_list');
  assert.deepEqual(received, {});
});

test('原生选择器取消属于正常结果', () => {
  assert.equal(isCancellation({ ok: true, data: { cancelled: true } }), true);
  assert.equal(isCancellation({ ok: true, data: { cancelled: false } }), false);
  assert.equal(isCancellation({ ok: false, error: 'x' }), false);
  assert.equal(isCancellation(null), false);
});
