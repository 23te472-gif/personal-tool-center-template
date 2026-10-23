import test from 'node:test';
import assert from 'node:assert/strict';
import {
  buildPackPayload,
  canStartPack,
  hasMissingFiles,
  isValidFile,
  jobStatusLabel,
  mergePickedFiles,
  missingFiles,
  normalizePathKey,
  removeFile,
  totalFileSize,
} from '../src/lib/pack.js';

const file = (path, size = 10, exists = true) => ({
  path,
  name: path.split(/[\\/]/).pop(),
  size,
  exists,
});

test('路径键在 Windows 上不区分大小写和斜杠', () => {
  assert.equal(normalizePathKey('C:/Docs/A.txt'), normalizePathKey('c:\\docs\\a.txt'));
});

test('追加选择会去重且保留已有顺序', () => {
  const existing = [file('C:\\Docs\\a.txt', 1), file('C:\\Docs\\b.txt', 2)];
  const incoming = [
    file('c:/docs/A.TXT', 999),
    file('C:\\Docs\\c.txt', 3),
    file('C:\\Docs\\b.txt', 2),
  ];
  const merged = mergePickedFiles(existing, incoming);
  assert.deepEqual(
    merged.map((item) => item.name),
    ['a.txt', 'b.txt', 'c.txt']
  );
  assert.equal(merged[0].size, 1);
});

test('无效文件被过滤，输入不会被修改', () => {
  const existing = [file('C:\\a.txt')];
  const snapshot = JSON.stringify(existing);
  const merged = mergePickedFiles(existing, [null, {}, { path: '   ' }, file('C:\\b.txt')]);
  assert.equal(merged.length, 2);
  assert.equal(JSON.stringify(existing), snapshot);
  assert.equal(isValidFile({ path: '' }), false);
});

test('移除文件不区分大小写，并过滤无效输入', () => {
  const files = [file('C:\\Docs\\a.txt'), file('C:\\Docs\\b.txt')];
  const next = removeFile(files, 'c:/docs/A.TXT');
  assert.deepEqual(next.map((item) => item.name), ['b.txt']);
  assert.deepEqual(removeFile(null, 'x'), []);
});

test('总大小只累计有效非负数值', () => {
  const files = [
    file('a', 10),
    file('b', 20),
    file('c', -5),
    file('d', '30'),
    file('e', Number.NaN),
  ];
  assert.equal(totalFileSize(files), 60);
  assert.equal(totalFileSize(null), 0);
});

test('缺失文件检测用于禁用开始按钮', () => {
  const files = [file('C:\\a.txt'), file('C:\\gone.txt', 0, false)];
  assert.equal(hasMissingFiles(files), true);
  assert.deepEqual(missingFiles(files).map((item) => item.name), ['gone.txt']);
  assert.equal(hasMissingFiles([file('C:\\a.txt')]), false);
});

test('pack_start 载荷来自选择列表，空输出目录交给后端默认', () => {
  const files = [file('C:\\a.txt'), file('C:\\b.txt')];
  assert.deepEqual(buildPackPayload(files, ''), {
    files: ['C:\\a.txt', 'C:\\b.txt'],
  });
  assert.deepEqual(buildPackPayload(files, '  C:\\Out  '), {
    files: ['C:\\a.txt', 'C:\\b.txt'],
    output_dir: 'C:\\Out',
  });
  assert.deepEqual(buildPackPayload([null, { path: '' }], ''), { files: [] });
});

test('开始条件综合选择、忙状态与缺失文件', () => {
  assert.equal(canStartPack([file('C:\\a.txt')]), true);
  assert.equal(canStartPack([]), false);
  assert.equal(canStartPack([file('C:\\a.txt')], { busy: true }), false);
  assert.equal(canStartPack([file('C:\\gone', 0, false)]), false);
});

test('任务状态文案覆盖契约状态', () => {
  assert.equal(jobStatusLabel('queued'), '排队中');
  assert.equal(jobStatusLabel('running'), '进行中');
  assert.equal(jobStatusLabel('completed'), '已完成');
  assert.equal(jobStatusLabel('failed'), '失败');
  assert.equal(jobStatusLabel('other'), '未知状态');
});
