declare module 'node-forge'

declare global {
  // 由 apk/nuxt.config.ts 的 vite.define 注入，网页构建下不存在
  const __IS_APK__: boolean
  // 由 desktop/nuxt.config.ts 的 vite.define 注入，仅在 EXE 桌面版存在
  const __IS_DESKTOP__: boolean

  interface Console {
    parse(v: any): void

    json(v: any, space: number): string
  }

  interface Window {
    umami: {
      track(name: string, data?: any): void
    }
    LA: any
    dataLayer: any
    JSZip: any
    disableEventListener?: boolean
  }

  interface ImportMeta {
    client: boolean
    server: boolean
    env: ImportMetaEnv
  }

  interface ImportMetaEnv {
    readonly VITE_PASSWORD_RSA_PUBLIC_KEY?: string
  }
}
export {}
