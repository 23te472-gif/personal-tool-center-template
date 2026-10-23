import { spawnSync } from 'node:child_process';
import { copyFile, mkdir, readFile, rm, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { resolveEsbuildBinary } from './esbuild-binary.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const dist = path.join(root, 'dist');
const assets = path.join(dist, 'assets');
const pkg = JSON.parse(await readFile(path.join(root, 'package.json'), 'utf8'));
const dev = process.argv.includes('--dev');

const esbuild = await resolveEsbuildBinary(root);

await rm(dist, { recursive: true, force: true });
await mkdir(assets, { recursive: true });

const args = [
  path.join(root, 'src/main.jsx'),
  '--bundle',
  `--outfile=${path.join(assets, 'app.js')}`,
  '--format=iife',
  '--target=chrome110,edge110',
  '--jsx=automatic',
  '--loader:.jsx=jsx',
  '--legal-comments=none',
  `--define:process.env.NODE_ENV="${dev ? 'development' : 'production'}"`,
  `--define:__APP_VERSION__="${pkg.version}"`,
  '--log-level=info',
];
if (!dev) args.push('--minify');
else args.push('--sourcemap=inline');

const result = spawnSync(esbuild, args, { cwd: root, stdio: 'inherit' });
if (result.error) throw result.error;
if (result.status !== 0) {
  throw new Error(`esbuild 构建失败，退出码 ${result.status}`);
}

await copyFile(path.join(root, 'src/index.html'), path.join(dist, 'index.html'));

const required = ['index.html', 'assets/app.js', 'assets/app.css'];
for (const relative of required) {
  const info = await stat(path.join(dist, relative));
  if (!info.isFile() || info.size === 0) {
    throw new Error(`构建产物缺失或为空：dist/${relative}`);
  }
}

const sizes = await Promise.all(
  required.map(async (relative) => {
    const info = await stat(path.join(dist, relative));
    return `${relative} ${(info.size / 1024).toFixed(1)} KiB`;
  })
);

console.log(`\n个人工具中心前端构建完成（${dev ? 'development' : 'production'}）`);
for (const line of sizes) console.log(`  ${line}`);
console.log(`  入口：${path.join(dist, 'index.html')}`);
