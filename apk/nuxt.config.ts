// APK 精简构建配置：仅保留词汇学习相关页面与资源
// 注意：此文件由 apk/build-web.mjs 在构建期间临时挂到根目录 nuxt.config.ts 使用
import { resolve } from 'node:path'
import Components from 'unplugin-vue-components/vite'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'
import baseConfig from '../nuxt.config.base'

const rootDir = resolve(__dirname, '..')
const apkDir = resolve(rootDir, 'apk')

// 需要保留的页面路由前缀
const keepRoutePrefixes = ['/words', '/words-test', '/dict', '/dict-list', '/practice-words']

// 被裁剪掉的功能页面，统一重定向到单词学习页，避免出现 404
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
  buildDir: resolve(rootDir, '.nuxt-apk'),
  dir: { layouts: resolve(apkDir, 'layouts') },
  // 本地 file:// 打包环境下使用 hash 路由，避免刷新/深链 404
  router: { options: { hashMode: true } },
  // 图片不做服务端优化，直接使用 public 下的原图
  image: { provider: 'none' },
  // 精简构建不覆盖项目的组件类型声明文件
  vite: {
    // 构建期标记，供业务代码裁剪仅网页端需要的内容（收藏引导、TTS 设置提示等）
    define: { __IS_APK__: 'true' },
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
    output: { dir: resolve(rootDir, '.output-apk') },
  },
  hooks: {
    'pages:extend'(pages) {
      for (let i = pages.length - 1; i >= 0; i--) {
        if (!isKeepRoute(pages[i].path)) pages.splice(i, 1)
      }
      pages.push({ name: 'apk-index', path: '/', redirect: '/words' } as any)
      legacyRedirects.forEach(path => {
        pages.push({ name: `apk-redirect-${path.slice(1)}`, path, redirect: '/words' } as any)
      })
    },
  },
})
