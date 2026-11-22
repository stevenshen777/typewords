<script setup lang="ts">
import { BaseIcon } from '@/base'
import useTheme from '@/core/hooks/theme.ts'
import { useSettingStore } from '@/core/stores/setting.ts'
import { ShortcutKey } from '@/core/types/enum.ts'
import { onMounted, watch } from 'vue'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import { useInit } from '@/core/composables/useInit.ts'
import { useI18n } from 'vue-i18n'
import WordCollectPopover from '@/components/word/WordCollectPopover.vue'
import { useRoute, useRouter } from 'vue-router'

const { toggleTheme, getTheme, setTheme } = useTheme()
const settingStore = useSettingStore()
const init = useInit()
const route = useRoute()
const router = useRouter()

// 任何页面都能一键回到单词主页
function goHome() {
  ;(document.activeElement as HTMLElement | null)?.blur()
  if (route.path === '/words') return
  router.push('/words')
}

// APK 版不展示左侧导航，占位宽度置 0，保证练习区/工具栏仍按居中计算
if (import.meta.client) {
  document.documentElement.style.setProperty('--aside-width', '0rem')
}

watch(
  () => settingStore.load,
  n => {
    if (!n) return
    setTheme(settingStore.theme)
  }
)

watch(
  () => settingStore.theme,
  n => {
    setTheme(n)
  }
)

const { locales, setLocale } = useI18n()

onMounted(() => {
  init()
})
</script>

<template>
  <div class="layout anim">
    <!-- 移动端顶部菜单栏 -->
    <div class="mobile-top-nav" :class="{ collapsed: settingStore.mobileNavCollapsed }">
      <div class="nav-items">
        <div class="nav-item active">
          <IconFluentTextUnderlineDouble20Regular />
          <span>{{ $t('words') }}</span>
        </div>
      </div>
      <div class="nav-toggle" @click="settingStore.mobileNavCollapsed = !settingStore.mobileNavCollapsed">
        <IconFluentChevronDown20Filled v-if="!settingStore.mobileNavCollapsed" />
        <IconFluentChevronUp20Filled v-else />
      </div>
    </div>

    <!-- 返回主页按钮：平板/手机上始终可见，保证任何页面都能退回 -->
    <div class="home-btn" v-if="route.path !== '/words'" @click="goHome" title="返回主页">
      <IconFluentHome16Regular />
      <span>主页</span>
    </div>

    <div class="flex-1 z-1 relative main-content overflow-x-hidden">
      <router-view></router-view>

      <div class="absolute right-4 top-4 flex z-1 gap-2">
        <div class="relative group">
          <BaseIcon>
            <IconPhTranslate />
          </BaseIcon>
          <div
            class="space-y-2 pt-2 absolute z-2 right-0 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 pointer-events-none group-hover:pointer-events-auto"
          >
            <div class="card mb-2 py-4 px-6 space-y-3">
              <div v-for="locale in locales" @click="setLocale(locale.code)" class="w-full cp break-keep black-link">
                {{ locale.name }}
              </div>
            </div>
          </div>
        </div>

        <BaseIcon
          :title="`${$t('toggle_theme')}(${settingStore.shortcutKeyMap[ShortcutKey.ToggleTheme]})`"
          @click="toggleTheme"
        >
          <IconFluentWeatherMoon16Regular v-if="getTheme() === 'light'" />
          <IconFluentWeatherSunny16Regular v-else />
        </BaseIcon>
      </div>
    </div>
    <WordCollectPopover />
  </div>
</template>

<style scoped lang="scss">
.layout {
  width: 100%;
  height: 100%;
  display: flex;
  background: var(--color-primary);
}

// 移动端顶部菜单栏
.mobile-top-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: var(--color-second);
  border-bottom: 1px solid var(--color-item-border);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transition: all 0.3s ease;

  .nav-items {
    display: flex;
    justify-content: space-around;
    padding: 0.5rem 0;

    .nav-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0.5rem;
      cursor: pointer;
      transition: all 0.2s;
      min-height: 44px;
      min-width: 44px;
      justify-content: center;
      position: relative;

      svg {
        font-size: 1.2rem;
        margin-bottom: 0.2rem;
        color: var(--color-main-text);
      }

      span {
        font-size: 0.7rem;
        color: var(--color-main-text);
        text-align: center;
      }

      &.active {
        svg,
        span {
          color: var(--color-select-bg);
        }
      }

      &:active {
        transform: scale(0.95);
      }
    }
  }

  .nav-toggle {
    position: absolute;
    bottom: -1.5rem;
    left: 50%;
    transform: translateX(-50%);
    background: var(--color-second);
    border: 1px solid var(--color-item-border);
    border-top: none;
    border-radius: 0 0 0.5rem 0.5rem;
    padding: 0.3rem 0.8rem;
    cursor: pointer;
    transition: all 0.3s;

    svg {
      font-size: 1rem;
      color: var(--color-main-text);
    }

    &:active {
      transform: translateX(-50%) scale(0.95);
    }
  }

  &.collapsed {
    transform: translateY(calc(-100% + 1.5rem));

    .nav-items {
      opacity: 0;
      pointer-events: none;
    }
  }
}

.main-content {
  // 移动端时为主内容区域添加顶部内边距，避免被顶部菜单遮挡
  @media (max-width: 768px) {
    padding-top: 4rem;
  }
}

// 返回主页按钮：平板/手机上始终可见
.home-btn {
  position: fixed;
  top: 0.8rem;
  left: 0.8rem;
  z-index: 1001;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.9rem;
  border-radius: 0.6rem;
  background: var(--color-second);
  border: 1px solid var(--color-item-border);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
  font-size: 0.85rem;
  color: var(--color-main-text);
  cursor: pointer;
  user-select: none;

  svg {
    font-size: 1.1rem;
  }

  &:active {
    transform: scale(0.95);
  }
}

// 移动端隐藏左侧菜单栏
@media (max-width: 768px) {
  .main-content {
    width: 100%;
    margin-left: 0;
  }
}

// 桌面端隐藏移动端顶部菜单栏
@media (min-width: 769px) {
  .mobile-top-nav {
    display: none;
  }
}
</style>

<style lang="scss">
// 软键盘弹出时，让出尽可能多的可视区域，避免单词被键盘/工具栏遮挡
html.soft-keyboard-open {
  .mobile-top-nav {
    transform: translateY(-100%) !important;
  }

  .main-content {
    padding-top: 0 !important;
  }

  .footer-wrap {
    display: none !important;
  }

  #PracticeArea {
    height: 100% !important;
    padding-bottom: 0 !important;
  }
}
</style>
