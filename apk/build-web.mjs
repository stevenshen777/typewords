// 生成 APK 用的精简静态站点：临时切换 nuxt.config -> 构建 -> 还原配置 -> 裁剪无关资源
import { spawnSync } from 'node:child_process'
import { cpSync, existsSync, mkdirSync, readdirSync, renameSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const apkDir = dirname(fileURLToPath(import.meta.url))
const rootDir = resolve(apkDir, '..')
const configPath = resolve(rootDir, 'nuxt.config.ts')
const baseConfigPath = resolve(rootDir, 'nuxt.config.base.ts')
const outputDir = resolve(rootDir, '.output-apk')
const wwwDir = resolve(apkDir, 'capacitor/www')

const TEMP_CONFIG = `// 临时文件：由 apk/build-web.mjs 生成，构建结束后自动删除
export { default } from './apk/nuxt.config'
`

function swapConfig() {
  if (!existsSync(baseConfigPath)) {
    renameSync(configPath, baseConfigPath)
  }
  writeFileSync(configPath, TEMP_CONFIG, 'utf8')
}

function restoreConfig() {
  if (existsSync(baseConfigPath)) {
    if (existsSync(configPath)) rmSync(configPath)
    renameSync(baseConfigPath, configPath)
  }
}

function run(command, args) {
  console.log(`\n> ${command} ${args.join(' ')}`)
  const result = spawnSync(command, args, { cwd: rootDir, stdio: 'inherit', env: process.env })
  if (result.status !== 0) {
    throw new Error(`命令执行失败: ${command} ${args.join(' ')}`)
  }
}

// 需要从 APK 中剔除的无关资源（相对 public 目录）
const EXCLUDED = [
  'dicts/en/article',
  'list/article.json',
  'list/recommend_article.json',
  'sound/article',
  '_redirects',
  'robots.txt',
]

function prepareWww() {
  const publicDir = resolve(outputDir, 'public')
  if (!existsSync(publicDir)) {
    throw new Error('未找到构建产物: ' + publicDir)
  }

  rmSync(wwwDir, { recursive: true, force: true })
  mkdirSync(wwwDir, { recursive: true })
  cpSync(publicDir, wwwDir, { recursive: true })

  for (const item of EXCLUDED) {
    rmSync(resolve(wwwDir, item), { recursive: true, force: true })
  }

  // 图片仅保留 Logo 与空状态插图
  const imgsDir = resolve(wwwDir, 'imgs')
  for (const name of readdirSync(imgsDir)) {
    if (name === 'logo' || name === 'empty.svg') continue
    rmSync(resolve(imgsDir, name), { recursive: true, force: true })
  }
}

swapConfig()
try {
  rmSync(outputDir, { recursive: true, force: true })
  rmSync(resolve(rootDir, '.nuxt-apk'), { recursive: true, force: true })
  run(process.execPath, [resolve(rootDir, 'node_modules/nuxt/bin/nuxt.mjs'), 'generate'])
  prepareWww()
  console.log('\n精简站点已生成: ' + wwwDir)
} finally {
  restoreConfig()
}
