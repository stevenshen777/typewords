import {onDeactivated, onMounted, onUnmounted, watch, type WatchSource} from 'vue'
import {emitter, EventKey} from '../utils/eventBus'
import {useSettingStore} from '../stores'
import {isMobile} from '../utils'
import {Toast} from '@/base'

const CODE_TO_CHAR: Record<string, string> = {
  ...Object.fromEntries('ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').map(c => [`Key${c}`, c.toLowerCase()])),
  ...Object.fromEntries(Array.from({ length: 10 }, (_, i) => [`Digit${i}`, String(i)])),
  ...Object.fromEntries(Array.from({ length: 10 }, (_, i) => [`Numpad${i}`, String(i)])),
  Minus: '-',
  Equal: '=',
  BracketLeft: '[',
  BracketRight: ']',
  Semicolon: ';',
  Quote: "'",
  Comma: ',',
  Period: '.',
  Slash: '/',
  Backslash: '\\',
  Space: ' ',
  Backspace: 'Backspace',
}

const SHIFT_CODE_TO_CHAR: Record<string, string> = {
  Digit1: '!',
  Digit2: '@',
  Digit3: '#',
  Digit4: '$',
  Digit5: '%',
  Digit6: '^',
  Digit7: '&',
  Digit8: '*',
  Digit9: '(',
  Digit0: ')',
  Minus: '_',
  Equal: '+',
  BracketLeft: '{',
  BracketRight: '}',
  Semicolon: ':',
  Quote: '"',
  Comma: '<',
  Period: '>',
  Slash: '?',
  Backslash: '|',
}

const CHAR_TO_CODE: Record<string, string> = {}
for (const [code, char] of Object.entries(CODE_TO_CHAR)) {
  CHAR_TO_CODE[char] = code
  if (code.startsWith('Key')) {
    CHAR_TO_CODE[char.toUpperCase()] = code
  }
}
for (const [code, char] of Object.entries(SHIFT_CODE_TO_CHAR)) {
  CHAR_TO_CODE[char] = code
}

function charToCode(char: string) {
  return CHAR_TO_CODE[char] ?? ''
}

function getSelectedText() {
  return window.getSelection().toString().trim()
}

export function useWindowClick(cb: (e: PointerEvent) => void) {
  const add = () => {
    emitter.on(EventKey.closeOther, cb)
    window.addEventListener('click', cb)
  }
  onMounted(add)
  // onActivated(add)

  const remove = () => {
    window.removeEventListener('click', cb)
  }
  onUnmounted(remove)
  onDeactivated(remove)
}

export function useEventListener(type: string, listener: EventListenerOrEventListenerObject) {
  const invokeListener = (event: KeyboardEvent) => {
    if (typeof listener === 'function') {
      return (listener as EventListener)(event)
    }
    if (listener && typeof (listener as EventListenerObject).handleEvent === 'function') {
      return (listener as EventListenerObject).handleEvent(event)
    }
  }

  let cleanup: (() => void) | null = null

  const add = () => {
    //chrome上，win的事件先触发，safari上input的事件先触发
    const emitWindowsKeys = new Set()
    const emitInputKeys = new Set()
    const cleanupFns: Array<() => void> = []
    const registerCleanup = (fn: () => void) => cleanupFns.push(fn)

    const performCleanup = () => {
      while (cleanupFns.length) {
        const fn = cleanupFns.pop()
        try {
          fn()
        } catch (err) {
          console.warn('[useEventListener] cleanup error', err)
        }
      }
    }

    if (type === 'keydown') {
      const ensureMobileInput = () => {
        let input = document.querySelector('#typing-listener') as HTMLInputElement | null
        if (!input) {
          input = document.createElement('input')
          input.id = 'typing-listener'
          input.type = 'text'
          input.autofocus = true
          input.autocomplete = 'off'
          input.autocapitalize = 'off'
          input.autocorrect = false
          input.spellcheck = false
          input.tabIndex = -1
          input.setAttribute('aria-hidden', 'true')
          Object.assign(input.style, {
            position: 'fixed',
            top: '50vh',
            left: '50vw',
            opacity: '0',
            pointerEvents: 'none',
            width: '1px',
            height: '1px',
            zIndex: '-1',
            // left: '-9999px',
          })
        }
        if (!input.parentNode) {
          document.body.appendChild(input)
        }
        setTimeout(() => {
          input.focus()
        }, 100)
        return input
      }

      const hiddenInput = ensureMobileInput()
      let isComposing = false
      // 软键盘（尤其 Android WebView）按退格时，IME 不会派发 keydown，
      // 只有当输入框「有内容可删」时才会触发 input(deleteContentBackward)。
      // 因此不主动清空输入框，而是维护一份缓冲，用值的增减来派发字母/退格，
      // 这样无论 Gboard 走组合输入还是直接插入，退格都能正确回退到上一个字母。
      let lastValue = ''

      const createSyntheticEvent = (payload: { key: string; code?: string; keyCode: number }) => {
        const base = {
          key: payload.key,
          code: payload.code ?? '',
          keyCode: payload.keyCode,
          which: payload.keyCode,
          ctrlKey: false,
          altKey: false,
          shiftKey: false,
          metaKey: false,
          repeat: false,
          isComposing: false,
          type,
          preventDefault() {},
          stopPropagation() {},
          stopImmediatePropagation() {},
        }
        return base as unknown as KeyboardEvent
      }

      const dispatchSyntheticKey = (payload: { key: string; code?: string; keyCode: number }) => {
        invokeListener(createSyntheticEvent(payload))
      }

      /** 派发单个字符，并与物理按键事件做去重 */
      const dispatchChar = (char: string) => {
        if (!char) return
        if (emitWindowsKeys.has(char)) return
        emitInputKeys.add(char)
        setTimeout(() => emitInputKeys.delete(char), 30)
        const keyCode =
          char === 'Backspace' ? 8 : char === ' ' ? 32 : char.toUpperCase().charCodeAt(0)
        dispatchSyntheticKey({ key: char, code: charToCode(char), keyCode })
      }

      const resetBuffer = () => {
        lastValue = ''
        if (hiddenInput.value) hiddenInput.value = ''
      }

      const commonPrefixLength = (a: string, b: string) => {
        let i = 0
        while (i < a.length && i < b.length && a.charCodeAt(i) === b.charCodeAt(i)) i++
        return i
      }

      // 用输入框值的变化量来派发字母 / 退格：
      // - 值变长 → 派发新增的字符（保持逐字变绿）
      // - 值变短 → 派发等量退格（修复软键盘退格无法回退）
      const applyValueDiff = (value: string) => {
        if (value === lastValue) return
        const prefix = commonPrefixLength(lastValue, value)
        const removedCount = lastValue.length - prefix
        for (let i = 0; i < removedCount; i++) {
          dispatchChar('Backspace')
        }
        const added = value.slice(prefix)
        let typedSpace = false
        for (const ch of added) {
          if (ch === ' ') typedSpace = true
          // 只上屏英文可输入字符，避免中文候选 / 表情进入单词
          if (!/[A-Za-z0-9 .,'\-]/.test(ch)) continue
          dispatchChar(ch)
        }
        lastValue = value
        // 空格结束当前单词，清空缓冲，避免退格误入上一个单词
        if (typedSpace) resetBuffer()
      }

      const handleCompositionStart = () => {
        isComposing = true
      }

      const handleCompositionEnd = (event: CompositionEvent) => {
        const data = event.data ?? ''
        isComposing = false
        // 中文等非英文组合输入上屏时提示切换英文输入法
        if (/[^\x20-\x7E]/.test(data)) {
          Toast.warning('请切换到英文输入')
          resetBuffer()
        }
      }

      const handleInput = (event: InputEvent) => {
        // 桌面端由物理键盘 keydown 直接处理，这里只服务移动 / APK 软键盘
        if (!isMobile()) return
        const target = event.target as HTMLInputElement | null
        if (!target) return
        applyValueDiff(target.value ?? '')
      }

      // 切换到下一个单词（或重置）时清空缓冲，防止退格作用到旧单词
      emitter.on(EventKey.resetWord, resetBuffer)
      registerCleanup(() => emitter.off(EventKey.resetWord, resetBuffer))

      const isPracticePage = () => /\/practice/.test(`${window.location.pathname}${window.location.hash}`)

      const handleFocusRequest = (event: MouseEvent | TouchEvent) => {
        const target = event.target as HTMLElement | null
        if (!target) return
        // hash 路由下 location.pathname 不含 /practice，需要一并判断 hash
        if (!isPracticePage()) return
        const typingWord = target.closest('#PracticeArea')
        if (!typingWord) return
        if (target.closest('input, textarea, select, [contenteditable="true"]')) return
        if (getSelectedText()) return
        // 安卓/Pad 的软键盘必须在用户手势内调用 focus 才会弹出，
        // 先同步聚焦一次，再兜底延迟聚焦，避免键盘被系统收回后无法再次唤起
        hiddenInput.focus()
        window.setTimeout(() => hiddenInput.focus(), 160)
      }

      const windowListener = (e: KeyboardEvent) => {
        if (e.key === 'Process') {
          return
        }
        if (emitInputKeys.has(e.key)) return
        // console.log('windowListener', Date.now(), emitInputKeys)
        invokeListener(e)
        emitWindowsKeys.add(e.key)
        setTimeout(() => emitWindowsKeys.delete(e.key), 30)
      }

      hiddenInput.addEventListener('compositionstart', handleCompositionStart)
      registerCleanup(() => hiddenInput.removeEventListener('compositionstart', handleCompositionStart))

      hiddenInput.addEventListener('compositionend', handleCompositionEnd)
      registerCleanup(() => hiddenInput.removeEventListener('compositionend', handleCompositionEnd))

      // 软键盘弹出时给根节点打标记，供 APK 布局收起顶部栏/底部工具栏，保证单词始终可见
      const onHiddenInputFocus = () => document.documentElement.classList.add('soft-keyboard-open')
      const onHiddenInputBlur = () => document.documentElement.classList.remove('soft-keyboard-open')

      hiddenInput.addEventListener('focus', onHiddenInputFocus)
      registerCleanup(() => hiddenInput.removeEventListener('focus', onHiddenInputFocus))

      hiddenInput.addEventListener('blur', onHiddenInputBlur)
      registerCleanup(() => hiddenInput.removeEventListener('blur', onHiddenInputBlur))

      hiddenInput.addEventListener('input', handleInput, { capture: true })
      registerCleanup(() => hiddenInput.removeEventListener('input', handleInput, { capture: true }))

      window.addEventListener('click', handleFocusRequest)
      registerCleanup(() => window.removeEventListener('click', handleFocusRequest))

      window.addEventListener('touchstart', handleFocusRequest)
      registerCleanup(() => window.removeEventListener('touchstart', handleFocusRequest))

      window.addEventListener(type, windowListener, { capture: true })
      registerCleanup(() => window.removeEventListener(type, windowListener, { capture: true }))

      registerCleanup(() => hiddenInput.remove())
    } else {
      const windowListener = (event: Event) => invokeListener(event as KeyboardEvent)
      window.addEventListener(type, windowListener, { capture: true })
      registerCleanup(() => window.removeEventListener(type, windowListener, { capture: true }))
    }

    cleanup = () => {
      performCleanup()
      cleanup = null
    }
  }
  onMounted(add)

  const remove = () => {
    if (cleanup) cleanup()
  }

  onUnmounted(remove)
  onDeactivated(remove)
}

export function getShortcutKey(e: KeyboardEvent) {
  let shortcutKey = ''
  if (e.ctrlKey || e.metaKey) shortcutKey += 'Ctrl+'
  if (e.altKey) shortcutKey += 'Alt+'
  if (e.shiftKey) shortcutKey += 'Shift+'
  if (e.key !== 'Control' && e.key !== 'Alt' && e.key !== 'Shift') {
    if (e.keyCode >= 65 && e.keyCode <= 90) {
      shortcutKey += e.key.toUpperCase()
    } else {
      if (e.key === 'ArrowRight') {
        shortcutKey += '➡'
      } else if (e.key === 'ArrowLeft') {
        shortcutKey += '⬅'
      } else if (e.key === 'ArrowUp') {
        shortcutKey += '⬆'
      } else if (e.key === 'ArrowDown') {
        shortcutKey += '⬇'
      } else {
        //当空格为快捷键时，key为一个空字符，而代码里面写的快捷键是Space，导致匹配不上
        shortcutKey += e.key.trim() || e.code
      }
    }
  }
  shortcutKey = shortcutKey.trim()

  // console.log('key', shortcutKey)
  return shortcutKey
}

export function useStartKeyboardEventListener() {
  const settingStore = useSettingStore()

  useEventListener('keydown', (e: KeyboardEvent) => {
    // console.log('keydown', e)
    // debugger
    //解决无法复制、全选的问题
    if ((e.ctrlKey || e.metaKey) && ['KeyC', 'KeyA', 'KeyD'].includes(e.code)) return
    if (!window?.disableEventListener) {
      let shortcutKey = getShortcutKey(e)
      // console.log('shortcutKey', shortcutKey)

      let shortcutEvent = []
      for (let [k, v] of Object.entries(settingStore.shortcutKeyMap)) {
        if (v === shortcutKey) {
          // console.log('快捷键', k,emitter.all.has(k))
          //必须是已监听的事件，才拦截并触发
          //因为在自测时，才会监听 1234 四个键，平时如果也拦截会导致无法输入1234
          if (emitter.all.has(k) && emitter.all.get(k)?.length) {
            shortcutEvent.push(k)
          }
        }
      }
      // console.log('shortcutEvent', shortcutEvent, settingStore.shortcutKeyMap, emitter.all)
      if (shortcutEvent.length > 0) {
        e.preventDefault()
        shortcutEvent.map(s => emitter.emit(s, e))
      } else {
        // 非英文模式下，输入区域的 keyCode 均为 229时，
        if (
          ((e.keyCode >= 65 && e.keyCode <= 90) ||
            (e.keyCode >= 48 && e.keyCode <= 57) ||
            (e.keyCode >= 96 && e.keyCode <= 105) ||
            // 空格键已经在上面处理过了
            e.code === 'Slash' ||
            e.code === 'Quote' ||
            e.code === 'Comma' ||
            e.code === 'BracketLeft' ||
            e.code === 'BracketRight' ||
            e.code === 'Period' ||
            e.code === 'Minus' ||
            e.code === 'Equal' ||
            e.code === 'Semicolon' ||
            e.code === 'Backspace' ||
            e.code === 'Space' ||
            // || e.code === 'Backquote'
            e.keyCode === 229) &&
          //当按下功能键时，不阻止事件传播
          !e.ctrlKey &&
          !e.altKey
        ) {
          if (isMobile() && e.keyCode === 229 && e.key === 'Unidentified') {
            // 安卓软键盘在keydown阶段不会提供字符，等待input/composition事件来派发实际输入
            return
          }
          e.preventDefault()
          emitter.emit(EventKey.onTyping, e)
        } else {
          emitter.emit(EventKey.keydown, e)
        }
      }
    }
  })
  useEventListener('keyup', (e: KeyboardEvent) => {
    if (!window?.disableEventListener) {
      emitter.emit(EventKey.keyup, e)
    }
  })
}

export function useOnKeyboardEventListener(onKeyDown: (e: KeyboardEvent) => void, onKeyUp: (e: KeyboardEvent) => void) {
  const add = () => {
    emitter.on(EventKey.keydown, onKeyDown)
    emitter.on(EventKey.keyup, onKeyUp)
  }
  onMounted(add)
  // onActivated(add)

  const remove = () => {
    emitter.off(EventKey.keydown, onKeyDown)
    emitter.off(EventKey.keyup, onKeyUp)
  }
  onUnmounted(remove)
  onDeactivated(remove)
}

//因为如果用useStartKeyboardEventListener局部变量控制，当出现多个hooks时就不行了，所以用全局变量来控制
export function useDisableEventListener(watchVal: WatchSource<unknown>) {
  if (typeof window === 'undefined') return
  watch(
    watchVal,
    n => {
      window.disableEventListener = Boolean(n)
    },
    { immediate: true }
  )

  onUnmounted(() => {
    window.disableEventListener = false
  })
}
