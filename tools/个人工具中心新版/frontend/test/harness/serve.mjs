import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * 独立的测试夹具服务器：仅在本地视觉/交互验证时使用。
 * 它把 test/fixtures/bootstrap.json 注入到模拟 bridge，生产 dist 不包含这些数据。
 *
 * 用法：node test/harness/serve.mjs [端口]
 */
const here = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(here, '..', '..');
const distRoot = path.join(frontendRoot, 'dist');
const fixturePath = path.join(frontendRoot, 'test', 'fixtures', 'bootstrap.json');
const port = Number(process.argv[2] || 4180);
const host = '127.0.0.1';

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
};

function harnessHtml() {
  return `<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>个人工具中心 - 测试夹具预览</title>
<link rel="stylesheet" href="/assets/app.css" />
<style>
  .fixture-badge{position:fixed;left:14px;bottom:14px;z-index:500;padding:6px 10px;border-radius:8px;background:#17252d;color:#fff;font:600 11px/1.4 "Segoe UI",sans-serif;opacity:.82;pointer-events:none}
</style>
</head>
<body>
<div id="root"><div class="boot-static"><span class="boot-static__mark"></span><p>正在载入测试夹具…</p></div></div>
<div class="fixture-badge">独立测试夹具 · 非生产数据</div>
<script src="/harness.js"></script>
<script src="/assets/app.js" defer></script>
</body>
</html>`;
}

function harnessScript(fixture) {
  return `
(() => {
  const fixture = ${JSON.stringify(fixture)};
  const clone = (value) => JSON.parse(JSON.stringify(value));
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const calls = [];
  let jobs = clone(fixture.jobs);
  let wheel = clone(fixture.wheel);
  let games = clone(fixture.games);
  let recent = clone(fixture.recent);

  window.__fixtureCalls = calls;
  window.pywebview = {
    api: {
      call: async (action, payload) => {
        calls.push({ action, payload: clone(payload || {}) });
        switch (action) {
          case 'bootstrap':
            return { ok: true, data: {
              app: clone(fixture.app),
              settings: clone(fixture.settings),
              tools: clone(fixture.tools),
              games: clone(games),
              materials: clone(fixture.materials),
              wheel: clone(wheel),
              jobs: clone(jobs),
              recent: clone(recent),
              pack: clone(fixture.pack),
              warnings: clone(fixture.warnings)
            } };
          case 'game_list':
            return { ok: true, data: { games: clone(games) } };
          case 'game_favorite': {
            const target = games.find((game) => String(game.id) === String(payload.id));
            if (target) target.favorite = Boolean(payload.favorite);
            return { ok: true, data: { games: clone(games) } };
          }
          case 'game_open':
          case 'materials_open':
          case 'job_open':
          case 'open_folder':
            return { ok: true, data: { message: '测试夹具：已模拟本地打开请求（不启动程序）。' } };
          case 'pick_files':
            return { ok: true, data: { cancelled: false, files: [
              { path: 'C:\\\\Fixture\\\\Docs\\\\extra.txt', name: 'extra.txt', size: 5120, exists: true }
            ] } };
          case 'pick_output':
            return { ok: true, data: { cancelled: false, path: 'C:\\\\Fixture\\\\Output2' } };
          case 'pack_start':
          case 'pack_materials': {
            const job = { id: 'job-harness-' + Date.now(), status: 'running', message: '正在压缩测试夹具…', progress: 42, result_path: '', error: '' };
            jobs = [...jobs, job];
            return { ok: true, data: { job } };
          }
          case 'job_status': {
            const job = jobs.find((item) => item.id === payload.id);
            if (!job) return { ok: false, error: '夹具任务不存在' };
            job.progress = Math.min(100, Number(job.progress || 0) + 17);
            if (job.progress >= 100) {
              job.status = 'completed';
              job.message = '测试夹具打包完成';
              job.result_path = 'C:\\\\Fixture\\\\Output\\\\harness.zip';
            }
            return { ok: true, data: { job: clone(job) } };
          }
          case 'wheel_save':
            wheel = { ...clone(payload.wheel), recent: wheel.recent };
            return { ok: true, data: { wheel: clone(wheel) } };
          case 'wheel_add':
            wheel.entries.push({ id: 'wheel-harness-' + Date.now(), name: String(payload.name || ''), appid: '', enabled: true });
            return { ok: true, data: { wheel: clone(wheel) } };
          case 'wheel_import':
            return { ok: true, data: { wheel: clone(wheel), added: 0, warnings: ['测试夹具：本机 Steam 候选已全部导入。'] } };
          case 'wheel_draw': {
            const pool = wheel.entries.filter((entry) => entry.enabled);
            if (!pool.length) return { ok: false, error: '没有可抽取的候选' };
            const entry = pool[0];
            window.__fixtureLastDraw = entry.name;
            return { ok: true, data: { entry: clone(entry), recent: [entry.name, ...wheel.recent].slice(0, 3), challenge: '测试夹具挑战' } };
          }
          case 'steam_open':
            return { ok: true, data: { message: '测试夹具：已模拟 Steam 启动请求（不启动程序）。' } };
          case 'settings_save':
            fixture.settings = { theme: payload.theme, font_scale: payload.font_scale };
            return { ok: true, data: { settings: clone(fixture.settings) } };
          case 'launch_tool':
            if (payload.id === 'games' || payload.id === 'delivery') {
              return { ok: true, data: { action: 'internal', page: payload.id === 'games' ? 'games' : 'pack' } };
            }
            return { ok: true, data: { action: 'started', message: '测试夹具：已模拟工具启动请求（不启动程序）。' } };
          case 'game_save':
          case 'game_add':
          case 'game_add_tool':
            return { ok: true, data: { cancelled: false, games: clone(games) } };
          case 'materials_choose':
            return { ok: true, data: { cancelled: true } };
          case 'pack_previous':
            return { ok: true, data: { files: clone(fixture.pack.files), output_dir: fixture.pack.output_dir } };
          default:
            return { ok: false, error: '测试夹具未实现动作：' + action };
        }
      }
    }
  };

  window.addEventListener('load', () => {
    const params = new URLSearchParams(location.search);
    const page = params.get('page') || 'overview';
    const labelMap = { overview: '概览', games: '游戏管家', pack: '文件打包', wheel: '游戏转盘', settings: '设置' };
    if (page !== 'overview') {
      const clickNav = () => {
        const target = [...document.querySelectorAll('.nav-item')].find((node) => node.textContent.includes(labelMap[page]));
        if (target) { target.click(); return true; }
        return false;
      };
      const waitNav = () => { if (!clickNav()) setTimeout(waitNav, 80); };
      setTimeout(waitNav, 120);
    }
    if (params.get('detail') === '1') {
      const clickDetail = () => {
        const target = [...document.querySelectorAll('.game-card button')].find((node) => node.textContent.includes('查看与启动'));
        if (target) { target.click(); return true; }
        return false;
      };
      const waitDetail = () => { if (!clickDetail()) setTimeout(waitDetail, 120); };
      setTimeout(waitDetail, 500);
    }
    if (params.get('draw') === '1') {
      const clickDraw = () => {
        const target = [...document.querySelectorAll('.wheel-page button')].find((node) => node.textContent.includes('开始抽取'));
        if (target) { target.click(); return true; }
        return false;
      };
      const waitDraw = () => { if (!clickDraw()) setTimeout(waitDraw, 150); };
      setTimeout(waitDraw, 600);
    }
  });
})();
`;
}

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url || '/', `http://${host}:${port}`);
    let pathname = decodeURIComponent(url.pathname);
    if (pathname === '/') pathname = '/index.html';

    if (pathname === '/index.html') {
      response.writeHead(200, { 'Content-Type': mime['.html'], 'Cache-Control': 'no-store' });
      response.end(harnessHtml());
      return;
    }

    if (pathname === '/harness.js') {
      const fixture = JSON.parse(await readFile(fixturePath, 'utf8'));
      response.writeHead(200, { 'Content-Type': mime['.js'], 'Cache-Control': 'no-store' });
      response.end(harnessScript(fixture));
      return;
    }

    if (pathname.startsWith('/assets/')) {
      const target = path.resolve(distRoot, `.${pathname}`);
      if (!target.startsWith(distRoot + path.sep)) throw new Error('forbidden');
      const info = await stat(target);
      if (!info.isFile()) throw new Error('not a file');
      const data = await readFile(target);
      response.writeHead(200, {
        'Content-Type': mime[path.extname(target)] || 'application/octet-stream',
        'Content-Length': data.length,
        'Cache-Control': 'no-store',
      });
      response.end(data);
      return;
    }

    response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Not found');
  } catch (error) {
    response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Not found');
  }
});

server.listen(port, host, () => {
  console.log(`测试夹具预览：http://${host}:${port}/`);
  console.log('该页面使用 test/fixtures/bootstrap.json，不属于生产界面。');
});
