# TypeWords 桌面版（EXE）打包

产物：`release/TypeWords.exe`（单文件，约 11 MB，内含整个静态站点与 8 本词库）。

## 组成

| 文件 | 作用 |
|---|---|
| `desktop/nuxt.config.ts` | 桌面版构建配置：`ssr: false`、只保留词汇学习相关路由、输出到 `.output-exe` |
| `desktop/layouts/default.vue` | 桌面版布局（沿用 APK 版，去掉左侧导航栏） |
| `desktop/TypeWordsLauncher.cs` | EXE 主体：读取内嵌 `payload.zip`，在 127.0.0.1 起 HTTP 服务并打开浏览器 |
| `desktop/build-exe.mjs` | 构建脚本：生成静态站点 → 裁剪资源 → 打 zip → 用 `csc` 编译成 exe |
| `desktop/www/` | 中间产物（静态站点文件），`--reuse` 时直接复用 |

## 构建

```powershell
cd D:\PycharmProgram\TypeWords
node desktop\build-exe.mjs          # 全量：nuxt generate + 打包 + 编译，约 3~5 分钟
node desktop\build-exe.mjs --reuse  # 复用 desktop\www，只重打 zip 并编译，约 10 秒
```

脚本会在构建期间临时把根目录 `nuxt.config.ts` 换成转发到 `desktop/nuxt.config.ts` 的包装文件，结束后自动还原（原文件暂存为 `nuxt.config.base.ts`）。

## 裁剪规则（`EXCLUDED`）

`public/` 下这些内容不进入 exe：`dicts/en/article`、`list/article.json`、`list/recommend_article.json`、`sound/article`、`_redirects`、`robots.txt`；`imgs/` 只保留 `logo/` 与 `empty.svg`。`dict_resource/`、`scripts/`、`node_modules/`、`apk/`、`.git/` 本来就不在静态产物里。

## 运行机制

- 启动时把 zip 全部解到内存（约 32 MB），按请求从内存直接返回，不落盘。
- 端口从 5567 起探测，被占用就顺延到 5600。
- `/_nuxt/` 下的哈希资源返回长期缓存头；其余 `no-cache`；未知路径回退 `index.html`（SPA 路由）。
- 关闭命令行窗口即退出（进程结束、端口释放）。

## 依赖

- 构建：Node 22 + 项目 `node_modules`、`.NET Framework 4.8` 的 `csc.exe`（`C:\Windows\Microsoft.NET\Framework64\v4.0.30319\`）。
- 运行：Windows x64 + 系统自带 .NET Framework 4.x，不需要 Node。
