import { existsSync } from 'node:fs';
import { readdir, realpath } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(import.meta.url);

/**
 * 找到 esbuild 的平台可执行文件。构建脚本直接以 inherit stdio 调用它，
 * 不依赖 pnpm 的 bin 包装脚本，也避开受限环境对 piped child_process 的限制。
 */
export async function resolveEsbuildBinary(root) {
  const platform = `${process.platform}-${process.arch}`;
  const binaryName =
    process.platform === 'win32' ? 'esbuild.exe' : path.join('bin', 'esbuild');
  const candidates = [];

  if (process.env.ESBUILD_BINARY_PATH) {
    candidates.push(process.env.ESBUILD_BINARY_PATH);
  }

  try {
    const packageJson = require.resolve('esbuild/package.json');
    const esbuildDir = path.dirname(await realpath(packageJson));
    const platformJson = require.resolve(`@esbuild/${platform}/package.json`, {
      paths: [esbuildDir],
    });
    candidates.push(path.join(path.dirname(platformJson), binaryName));
  } catch {
    // 继续尝试扫描 pnpm 虚拟目录。
  }

  const pnpmDir = path.join(root, 'node_modules', '.pnpm');
  if (existsSync(pnpmDir)) {
    const entries = await readdir(pnpmDir);
    const prefix = `@esbuild+${platform}@`;
    for (const entry of entries) {
      if (!entry.startsWith(prefix)) continue;
      candidates.push(
        path.join(pnpmDir, entry, 'node_modules', '@esbuild', platform, binaryName)
      );
    }
  }

  for (const candidate of candidates) {
    if (candidate && existsSync(candidate)) return candidate;
  }

  throw new Error(
    '找不到 esbuild 平台可执行文件。请在本目录执行 pnpm install（官方 registry），' +
      '并确认 pnpm-workspace.yaml 的 allowBuilds 配置。'
  );
}
