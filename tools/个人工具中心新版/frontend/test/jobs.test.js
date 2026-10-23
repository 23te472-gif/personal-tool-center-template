import test from 'node:test';
import assert from 'node:assert/strict';
import {
  findJob,
  getActiveJobIds,
  getActiveJobs,
  isActiveJob,
  isTerminalJob,
  jobProgress,
  latestJob,
  shouldPollJobs,
  upsertJob,
} from '../src/lib/jobs.js';

const job = (id, status, extra = {}) => ({
  id,
  status,
  message: '',
  progress: 0,
  result_path: '',
  error: '',
  ...extra,
});

test('只有 queued/running 被视为活动任务', () => {
  assert.equal(isActiveJob(job('1', 'queued')), true);
  assert.equal(isActiveJob(job('2', 'running')), true);
  assert.equal(isActiveJob(job('3', 'completed')), false);
  assert.equal(isActiveJob(job('4', 'failed')), false);
  assert.equal(isActiveJob(null), false);
  assert.equal(isTerminalJob(job('5', 'completed')), true);
  assert.equal(isTerminalJob(job('6', 'failed')), true);
  assert.equal(isTerminalJob(job('7', 'running')), false);
});

test('任务列表筛选与轮询条件', () => {
  const jobs = [
    job('a', 'queued'),
    job('b', 'completed'),
    job('c', 'running'),
    job('d', 'failed'),
  ];
  assert.deepEqual(getActiveJobIds(jobs), ['a', 'c']);
  assert.equal(getActiveJobs(jobs).length, 2);
  assert.equal(shouldPollJobs(jobs), true);
  assert.equal(shouldPollJobs([job('x', 'completed')]), false);
  assert.equal(shouldPollJobs([]), false);
  assert.equal(shouldPollJobs(null), false);
});

test('进度按 0–100 百分比展示并夹紧范围', () => {
  assert.equal(jobProgress(job('1', 'running', { progress: 0 })), 0);
  assert.equal(jobProgress(job('2', 'running', { progress: 47.6 })), 48);
  assert.equal(jobProgress(job('3', 'running', { progress: 100 })), 100);
  assert.equal(jobProgress(job('4', 'running', { progress: 140 })), 100);
  assert.equal(jobProgress(job('5', 'running', { progress: -3 })), 0);
  assert.equal(jobProgress(job('6', 'running', { progress: 'bad' })), 0);
  assert.equal(jobProgress(null), 0);
});

test('upsertJob 追加或合并，保持原数组不可变', () => {
  const original = [job('a', 'queued', { progress: 10 })];
  const appended = upsertJob(original, job('b', 'running'));
  assert.equal(original.length, 1);
  assert.equal(appended.length, 2);

  const updated = upsertJob(appended, job('a', 'running', { progress: 55, message: 'x' }));
  assert.equal(updated[0].status, 'running');
  assert.equal(updated[0].progress, 55);
  assert.equal(updated[0].message, 'x');
  assert.equal(updated[0].result_path, '');
  assert.notEqual(updated, appended);

  assert.deepEqual(upsertJob(null, job('c', 'queued')).length, 1);
  assert.deepEqual(upsertJob(original, null), original);
});

test('查找最新任务与按 id 查找', () => {
  const jobs = [job('a', 'completed'), job('b', 'running')];
  assert.equal(latestJob(jobs).id, 'b');
  assert.equal(latestJob([]), null);
  assert.equal(findJob(jobs, 'a').status, 'completed');
  assert.equal(findJob(jobs, 'missing'), null);
  assert.equal(findJob(null, 'a'), null);
});
