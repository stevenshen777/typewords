// 把 TypeWords 打包成 Windows 单文件 EXE：
// 1) 用 desktop/nuxt.config.ts 生成纯前端静态站点（只保留词汇学习相关页面）
// 2) 裁剪与词汇学习无关的资源
// 3) 打成 payload.zip 内嵌进 C# 启动器，csc 编译出 dist/TypeWords.exe
import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, renameSync, rmSync, writeFileSync, readFileSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { deflateRawSync, crc32 } from 'node:zlib'

const desktopDir = dirname(fileURLToPath(import.meta.url))
const rootDir = resolve(desktopDir, '..')
const configPath = resolve(rootDir, 'nuxt.config.ts')
const baseConfigPath = resolve(rootDir, 'nuxt.config.base.ts')
const outputDir = resolve(rootDir, '.output-exe')
const wwwDir = resolve(desktopDir, 'www')
const zipPath = resolve(desktopDir, 'payload.zip')
const distDir = resolve(rootDir, 'release')
const exePath = resolve(distDir, 'TypeWords.exe')
const CSC = 'C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\csc.exe'

const TEMP_CONFIG = `// 临时文件：由 desktop/build-exe.mjs 生成，构建结束后自动删除
export { default } from './desktop/nuxt.config'
`

// 与词汇学习无关、不打包的资源（相对 public 目录）
const EXCLUDED = [
  'dicts/en/article',
  'list/article.json',
  'list/recommend_article.json',
  'sound/article',
  '_redirects',
  'robots.txt',
]

function swapConfig() {
  if (!existsSync(baseConfigPath)) renameSync(configPath, baseConfigPath)
  writeFileSync(configPath, TEMP_CONFIG, 'utf8')
}

function restoreConfig() {
  if (existsSync(baseConfigPath)) {
    if (existsSync(configPath)) rmSync(configPath, { force: true })
    renameSync(baseConfigPath, configPath)
  }
}

function run(cmd, args, env) {
  console.log(`\n> ${cmd} ${args.join(' ')}`)
  const r = spawnSync(cmd, args, {
    cwd: rootDir,
    stdio: 'inherit',
    env: env || process.env,
  })
  if (r.status !== 0) throw new Error('命令执行失败: ' + cmd)
}

function prune() {
  const publicDir = resolve(outputDir, 'public')
  if (!existsSync(publicDir)) throw new Error('未找到构建产物: ' + publicDir)

  rmSync(wwwDir, { recursive: true, force: true })
  mkdirSync(wwwDir, { recursive: true })
  // 复制（不跟随符号链接）
  const stack = ['']
  while (stack.length) {
    const rel = stack.pop()
    const srcDir = resolve(publicDir, rel)
    if (!existsSync(srcDir)) continue
    for (const ent of readdirSync(srcDir, { withFileTypes: true })) {
      const childRel = rel ? `${rel}/${ent.name}` : ent.name
      const src = resolve(publicDir, childRel)
      const dst = resolve(wwwDir, childRel)
      if (ent.isDirectory()) {
        mkdirSync(dst, { recursive: true })
        stack.push(childRel)
      } else if (ent.isFile()) {
        mkdirSync(dirname(dst), { recursive: true })
        writeFileSync(dst, readFileSync(src))
      }
    }
  }

  for (const item of EXCLUDED) rmSync(resolve(wwwDir, item), { recursive: true, force: true })

  const imgsDir = resolve(wwwDir, 'imgs')
  if (existsSync(imgsDir)) {
    for (const name of readdirSync(imgsDir)) {
      if (name === 'logo' || name === 'empty.svg') continue
      rmSync(resolve(imgsDir, name), { recursive: true, force: true })
    }
  }
}

function collectFiles(dir, base, out) {
  for (const ent of readdirSync(dir, { withFileTypes: true })) {
    const full = resolve(dir, ent.name)
    if (ent.isDirectory()) collectFiles(full, base, out)
    else if (ent.isFile()) out.push({ name: relative(base, full).replace(/\\/g, '/'), data: readFileSync(full) })
  }
  return out
}

function dosTime(d) {
  const time = (d.getHours() << 11) | (d.getMinutes() << 5) | Math.floor(d.getSeconds() / 2)
  const date = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate()
  return { time, date }
}

function buildZip(entries) {
  const now = dosTime(new Date())
  const locals = []
  const centrals = []
  let offset = 0

  for (const e of entries) {
    const comp = deflateRawSync(e.data, { level: 9 })
    const crc = crc32(e.data) >>> 0
    const nameBuf = Buffer.from(e.name, 'utf8')

    const lh = Buffer.alloc(30)
    lh.writeUInt32LE(0x04034b50, 0)
    lh.writeUInt16LE(20, 4)
    lh.writeUInt16LE(0x0800, 6)
    lh.writeUInt16LE(8, 8)
    lh.writeUInt16LE(now.time, 10)
    lh.writeUInt16LE(now.date, 12)
    lh.writeUInt32LE(crc, 14)
    lh.writeUInt32LE(comp.length, 18)
    lh.writeUInt32LE(e.data.length, 22)
    lh.writeUInt16LE(nameBuf.length, 26)
    lh.writeUInt16LE(0, 28)

    locals.push(lh, nameBuf, comp)

    const ch = Buffer.alloc(46)
    ch.writeUInt32LE(0x02014b50, 0)
    ch.writeUInt16LE(20, 4)
    ch.writeUInt16LE(20, 6)
    ch.writeUInt16LE(0x0800, 8)
    ch.writeUInt16LE(8, 10)
    ch.writeUInt16LE(now.time, 12)
    ch.writeUInt16LE(now.date, 14)
    ch.writeUInt32LE(crc, 16)
    ch.writeUInt32LE(comp.length, 20)
    ch.writeUInt32LE(e.data.length, 24)
    ch.writeUInt16LE(nameBuf.length, 28)
    ch.writeUInt16LE(0, 30)
    ch.writeUInt16LE(0, 32)
    ch.writeUInt16LE(0, 34)
    ch.writeUInt16LE(0, 36)
    ch.writeUInt32LE(0, 38)
    ch.writeUInt32LE(offset, 42)
    centrals.push(ch, nameBuf)

    offset += lh.length + nameBuf.length + comp.length
  }

  const cd = Buffer.concat(centrals)
  const eocd = Buffer.alloc(22)
  eocd.writeUInt32LE(0x06054b50, 0)
  eocd.writeUInt16LE(0, 4)
  eocd.writeUInt16LE(0, 6)
  eocd.writeUInt16LE(entries.length, 8)
  eocd.writeUInt16LE(entries.length, 10)
  eocd.writeUInt32LE(cd.length, 12)
  eocd.writeUInt32LE(offset, 16)
  eocd.writeUInt16LE(0, 20)

  return Buffer.concat([...locals, cd, eocd])
}

function main() {
  if (!existsSync(CSC)) throw new Error('未找到 csc.exe（需要 .NET Framework 4.x）')

  const reuse = process.argv.includes('--reuse') && existsSync(resolve(wwwDir, 'index.html'))
  if (!reuse) {
    swapConfig()
  }
  try {
    if (!reuse) {
      rmSync(outputDir, { recursive: true, force: true })
      rmSync(resolve(rootDir, '.nuxt-exe'), { recursive: true, force: true })
      run(process.execPath, [resolve(rootDir, 'node_modules/nuxt/bin/nuxt.mjs'), 'generate'], {
        ...process.env,
        NODE_ENV: 'production',
      })

      prune()
    } else {
      console.log('\n[复用] 使用已有的 desktop/www 站点文件')
    }
    const entries = collectFiles(wwwDir, wwwDir, [])
    const zip = buildZip(entries)
    writeFileSync(zipPath, zip)
    const mb = (n) => (n / 1024 / 1024).toFixed(1) + ' MB'
    console.log(`\n[打包] ${entries.length} 个文件 -> payload.zip ${mb(zip.length)}`)

    mkdirSync(distDir, { recursive: true })
    const cscArgs = [
      '/nologo',
      '/target:exe',
      '/platform:x64',
      '/optimize+',
      '/codepage:65001',
      `/out:${exePath}`,
      `/resource:${zipPath},payload.zip`,
      '/r:System.IO.Compression.dll',
      '/r:System.IO.Compression.FileSystem.dll',
    ]
    const icon = resolve(desktopDir, 'app.ico')
    if (existsSync(icon)) cscArgs.push(`/win32icon:${icon}`)
    cscArgs.push(resolve(desktopDir, 'TypeWordsLauncher.cs'))
    run(CSC, cscArgs)
    console.log(`\n[完成] ${exePath} ${mb(readFileSync(exePath).length)}`)
  } finally {
    restoreConfig()
    rmSync(zipPath, { force: true })
  }
}

main()
