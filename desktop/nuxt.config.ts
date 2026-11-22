// 桌面版（EXE）精简构建配置：只保留词汇学习相关页面与资源
// 由 desktop/build-exe.mjs 在构建期间临时挂到根目录 nuxt.config.ts 使用
import { resolve } from 'node:path'
import Components from 'unplugin-vue-components/vite'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'
import baseConfig from '../nuxt.config.base'

const rootDir = resolve(__dirname, '..')
const desktopDir = resolve(rootDir, 'desktop')

const keepRoutePrefixes = ['/words', '/words-test', '/dict', '/dict-list', '/practice-words']

const legacyRedirects = [
  '/setting',
  '/articles',
  '/book-list',
  '/book',
  '/practice-articles',
  '/about',
  '/doc',
  '/feedback',
  '/help',
]

function isKeepRoute(path: string) {
  return keepRoutePrefixes.some(prefix => path === prefix || path.startsWith(`${prefix}/`))
}

export default defineNuxtConfig({
  ...baseConfig,
  ssr: false,
  devtools: { enabled: false },
  buildDir: resolve(rootDir, '.nuxt-exe'),
  dir: { layouts: resolve(desktopDir, 'layouts') },
  // 桌面版由内嵌 HTTP 服务承载，使用 history 路由，深链由服务端回退到 index.html
  image: { provider: 'none' },
  vite: {
    // 桌面版由本地服务承载，不需要「收藏本站」这类浏览器引导
    define: { __IS_DESKTOP__: 'true' },
    plugins: [
      Components({
        resolvers: [IconsResolver({ prefix: 'Icon' })],
        dts: false,
      }),
      Icons({ autoInstall: true }),
    ],
  },
  app: {
    ...baseConfig.app,
    baseURL: '/',
    head: {
      ...baseConfig.app?.head,
      title: 'Type Words',
      link: [{ rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }],
    },
  },
  i18n: {
    ...baseConfig.i18n,
    locales: [
      { code: 'zh', language: 'zh-CN', file: 'zh.json', name: '中文' },
      { code: 'en', language: 'en-US', file: 'en.json', name: 'English' },
    ],
    defaultLocale: 'zh',
  },
  routeRules: {
    '/**': { ssr: false },
  },
  nitro: {
    ...baseConfig.nitro,
    prerender: { routes: [], ignore: [] },
    output: { dir: resolve(rootDir, '.output-exe') },
  },
  hooks: {
    'pages:extend'(pages) {
      for (let i = pages.length - 1; i >= 0; i--) {
        if (!isKeepRoute(pages[i].path)) pages.splice(i, 1)
      }
      pages.push({ name: 'desktop-index', path: '/', redirect: '/words' } as any)
      legacyRedirects.forEach(path => {
        pages.push({ name: `desktop-redirect-${path.slice(1)}`, path, redirect: '/words' } as any)
      })
    },
  },
})
