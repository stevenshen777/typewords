
import type { DefineComponent, SlotsType } from 'vue'
type IslandComponent<T> = DefineComponent<{}, {refresh: () => Promise<void>}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, SlotsType<{ fallback: { error: unknown } }>> & T

type HydrationStrategies = {
  hydrateOnVisible?: IntersectionObserverInit | true
  hydrateOnIdle?: number | true
  hydrateOnInteraction?: keyof HTMLElementEventMap | Array<keyof HTMLElementEventMap> | true
  hydrateOnMediaQuery?: string
  hydrateAfter?: number
  hydrateWhen?: boolean
  hydrateNever?: true
}
type LazyComponent<T> = DefineComponent<HydrationStrategies, {}, {}, {}, {}, {}, {}, { hydrated: () => void }> & T

interface _GlobalComponents {
  About: typeof import("../../app/components/About.vue")['default']
  BaseTable: typeof import("../../app/components/BaseTable.vue")['default']
  Book: typeof import("../../app/components/Book.vue")['default']
  EditAbleText: typeof import("../../app/components/EditAbleText.vue")['default']
  Empty: typeof import("../../app/components/Empty.vue")['default']
  Header: typeof import("../../app/components/Header.vue")['default']
  Logo: typeof import("../../app/components/Logo.vue")['default']
  MiniProgram: typeof import("../../app/components/MiniProgram.vue")['default']
  Panel: typeof import("../../app/components/Panel.vue")['default']
  PracticeLayout: typeof import("../../app/components/PracticeLayout.vue")['default']
  ResourceCard: typeof import("../../app/components/ResourceCard.vue")['default']
  StageProgress: typeof import("../../app/components/StageProgress.vue")['default']
  ArticleAudio: typeof import("../../app/components/article/ArticleAudio.vue")['default']
  EditArticle: typeof import("../../app/components/article/EditArticle.vue")['default']
  EditBook: typeof import("../../app/components/article/EditBook.vue")['default']
  EditSingleArticleModal: typeof import("../../app/components/article/EditSingleArticleModal.vue")['default']
  QuestionForm: typeof import("../../app/components/article/QuestionForm.vue")['default']
  QuestionItem: typeof import("../../app/components/article/QuestionItem.vue")['default']
  Space: typeof import("../../app/components/article/Space.vue")['default']
  TypingArticle: typeof import("../../app/components/article/TypingArticle.vue")['default']
  TypingWord: typeof import("../../app/components/article/TypingWord.vue")['default']
  ChannelIcons: typeof import("../../app/components/channel-icons/ChannelIcons.vue")['default']
  Github: typeof import("../../app/components/channel-icons/Github.vue")['default']
  ShareIcon: typeof import("../../app/components/channel-icons/ShareIcon.vue")['default']
  WeChat: typeof import("../../app/components/channel-icons/WeChat.vue")['default']
  BackupGateDialog: typeof import("../../app/components/dialog/BackupGateDialog.vue")['default']
  CollectNotice: typeof import("../../app/components/dialog/CollectNotice.vue")['default']
  ConflictNotice: typeof import("../../app/components/dialog/ConflictNotice.vue")['default']
  ConflictNotice2: typeof import("../../app/components/dialog/ConflictNotice2.vue")['default']
  ConflictNoticeText: typeof import("../../app/components/dialog/ConflictNoticeText.vue")['default']
  IeDialog: typeof import("../../app/components/dialog/IeDialog.vue")['default']
  MigrateDialog: typeof import("../../app/components/dialog/MigrateDialog.vue")['default']
  WordFailedTable: typeof import("../../app/components/import/WordFailedTable.vue")['default']
  ArticleList: typeof import("../../app/components/list/ArticleList.vue")['default']
  BaseList: typeof import("../../app/components/list/BaseList.vue")['default']
  DictGroup: typeof import("../../app/components/list/DictGroup.vue")['default']
  DictList: typeof import("../../app/components/list/DictList.vue")['default']
  List: typeof import("../../app/components/list/List.vue")['default']
  WordList: typeof import("../../app/components/list/WordList.vue")['default']
  TypingArticleWord: typeof import("../../app/components/practice-sentences/TypingArticleWord.vue")['default']
  TypingSentence: typeof import("../../app/components/practice-sentences/TypingSentence.vue")['default']
  TypingSentenceItem: typeof import("../../app/components/practice-sentences/TypingSentenceItem.vue")['default']
  ArticleSetting: typeof import("../../app/components/setting/ArticleSetting.vue")['default']
  CommonSetting: typeof import("../../app/components/setting/CommonSetting.vue")['default']
  FsrsSetting: typeof import("../../app/components/setting/FsrsSetting.vue")['default']
  Log: typeof import("../../app/components/setting/Log.vue")['default']
  SettingDialog: typeof import("../../app/components/setting/SettingDialog.vue")['default']
  SettingItem: typeof import("../../app/components/setting/SettingItem.vue")['default']
  SoundMasterControl: typeof import("../../app/components/setting/SoundMasterControl.vue")['default']
  SoundSetting: typeof import("../../app/components/setting/SoundSetting.vue")['default']
  WordSetting: typeof import("../../app/components/setting/WordSetting.vue")['default']
  ChangeLastPracticeIndexDialog: typeof import("../../app/components/word/ChangeLastPracticeIndexDialog.vue")['default']
  ClickableEnglishText: typeof import("../../app/components/word/ClickableEnglishText.vue")['default']
  ClickableWord: typeof import("../../app/components/word/ClickableWord.vue")['default']
  Footer: typeof import("../../app/components/word/Footer.vue")['default']
  GroupList: typeof import("../../app/components/word/GroupList.vue")['default']
  PracticeOnboardingHost: typeof import("../../app/components/word/PracticeOnboardingHost.vue")['default']
  PracticeSettingDialog: typeof import("../../app/components/word/PracticeSettingDialog.vue")['default']
  PracticeWordListDialog: typeof import("../../app/components/word/PracticeWordListDialog.vue")['default']
  PrevAndNextWord: typeof import("../../app/components/word/PrevAndNextWord.vue")['default']
  SentenceHightLightWord: typeof import("../../app/components/word/SentenceHightLightWord.vue")['default']
  ShufflePracticeSettingDialog: typeof import("../../app/components/word/ShufflePracticeSettingDialog.vue")['default']
  Statistics: typeof import("../../app/components/word/Statistics.vue")['default']
  TranslationList: typeof import("../../app/components/word/TranslationList.vue")['default']
  TypeWord: typeof import("../../app/components/word/TypeWord.vue")['default']
  VolumeSettingMiniDialog: typeof import("../../app/components/word/VolumeSettingMiniDialog.vue")['default']
  WordCollectPopover: typeof import("../../app/components/word/WordCollectPopover.vue")['default']
  WordIdentifyPanel: typeof import("../../app/components/word/WordIdentifyPanel.vue")['default']
  WordItem: typeof import("../../app/components/word/WordItem.vue")['default']
  WordLookupPopover: typeof import("../../app/components/word/WordLookupPopover.vue")['default']
  WordMarkPickList: typeof import("../../app/components/word/WordMarkPickList.vue")['default']
  WordMetaPanel: typeof import("../../app/components/word/WordMetaPanel.vue")['default']
  WordTypingCore: typeof import("../../app/components/word/WordTypingCore.vue")['default']
  UnoIcon: typeof import("../../node_modules/.pnpm/@unocss+nuxt@66.7.5_@unocss_c117d2ce13d61ecf3be709a2b0933c47/node_modules/@unocss/nuxt/runtime/UnoIcon.vue")['default']
  NuxtWelcome: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/welcome.vue")['default']
  NuxtLayout: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-layout")['default']
  NuxtErrorBoundary: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']
  ClientOnly: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/client-only")['default']
  DevOnly: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/dev-only")['default']
  ServerPlaceholder: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/server-placeholder")['default']
  NuxtLink: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-link")['default']
  NuxtLoadingIndicator: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']
  NuxtTime: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']
  NuxtRouteAnnouncer: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']
  NuxtAnnouncer: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-announcer")['default']
  NuxtImg: typeof import("../../node_modules/.pnpm/@nuxt+image@2.0.0_@netlify+_247824bac513322053baf33987543c67/node_modules/@nuxt/image/dist/runtime/components/NuxtImg.vue")['default']
  NuxtPicture: typeof import("../../node_modules/.pnpm/@nuxt+image@2.0.0_@netlify+_247824bac513322053baf33987543c67/node_modules/@nuxt/image/dist/runtime/components/NuxtPicture.vue")['default']
  NuxtLinkLocale: typeof import("../../node_modules/.pnpm/@nuxtjs+i18n@10.2.1_@emnapi_7ce8fc2bbc29d6e7498c4a27e82f17ab/node_modules/@nuxtjs/i18n/dist/runtime/components/NuxtLinkLocale")['default']
  SwitchLocalePathLink: typeof import("../../node_modules/.pnpm/@nuxtjs+i18n@10.2.1_@emnapi_7ce8fc2bbc29d6e7498c4a27e82f17ab/node_modules/@nuxtjs/i18n/dist/runtime/components/SwitchLocalePathLink")['default']
  NuxtPage: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/pages/runtime/page")['default']
  NoScript: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['NoScript']
  Link: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Link']
  Base: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Base']
  Title: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Title']
  Meta: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Meta']
  Style: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Style']
  Head: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Head']
  Html: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Html']
  Body: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Body']
  NuxtIsland: typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-island")['default']
  LazyAbout: LazyComponent<typeof import("../../app/components/About.vue")['default']>
  LazyBaseTable: LazyComponent<typeof import("../../app/components/BaseTable.vue")['default']>
  LazyBook: LazyComponent<typeof import("../../app/components/Book.vue")['default']>
  LazyEditAbleText: LazyComponent<typeof import("../../app/components/EditAbleText.vue")['default']>
  LazyEmpty: LazyComponent<typeof import("../../app/components/Empty.vue")['default']>
  LazyHeader: LazyComponent<typeof import("../../app/components/Header.vue")['default']>
  LazyLogo: LazyComponent<typeof import("../../app/components/Logo.vue")['default']>
  LazyMiniProgram: LazyComponent<typeof import("../../app/components/MiniProgram.vue")['default']>
  LazyPanel: LazyComponent<typeof import("../../app/components/Panel.vue")['default']>
  LazyPracticeLayout: LazyComponent<typeof import("../../app/components/PracticeLayout.vue")['default']>
  LazyResourceCard: LazyComponent<typeof import("../../app/components/ResourceCard.vue")['default']>
  LazyStageProgress: LazyComponent<typeof import("../../app/components/StageProgress.vue")['default']>
  LazyArticleAudio: LazyComponent<typeof import("../../app/components/article/ArticleAudio.vue")['default']>
  LazyEditArticle: LazyComponent<typeof import("../../app/components/article/EditArticle.vue")['default']>
  LazyEditBook: LazyComponent<typeof import("../../app/components/article/EditBook.vue")['default']>
  LazyEditSingleArticleModal: LazyComponent<typeof import("../../app/components/article/EditSingleArticleModal.vue")['default']>
  LazyQuestionForm: LazyComponent<typeof import("../../app/components/article/QuestionForm.vue")['default']>
  LazyQuestionItem: LazyComponent<typeof import("../../app/components/article/QuestionItem.vue")['default']>
  LazySpace: LazyComponent<typeof import("../../app/components/article/Space.vue")['default']>
  LazyTypingArticle: LazyComponent<typeof import("../../app/components/article/TypingArticle.vue")['default']>
  LazyTypingWord: LazyComponent<typeof import("../../app/components/article/TypingWord.vue")['default']>
  LazyChannelIcons: LazyComponent<typeof import("../../app/components/channel-icons/ChannelIcons.vue")['default']>
  LazyGithub: LazyComponent<typeof import("../../app/components/channel-icons/Github.vue")['default']>
  LazyShareIcon: LazyComponent<typeof import("../../app/components/channel-icons/ShareIcon.vue")['default']>
  LazyWeChat: LazyComponent<typeof import("../../app/components/channel-icons/WeChat.vue")['default']>
  LazyBackupGateDialog: LazyComponent<typeof import("../../app/components/dialog/BackupGateDialog.vue")['default']>
  LazyCollectNotice: LazyComponent<typeof import("../../app/components/dialog/CollectNotice.vue")['default']>
  LazyConflictNotice: LazyComponent<typeof import("../../app/components/dialog/ConflictNotice.vue")['default']>
  LazyConflictNotice2: LazyComponent<typeof import("../../app/components/dialog/ConflictNotice2.vue")['default']>
  LazyConflictNoticeText: LazyComponent<typeof import("../../app/components/dialog/ConflictNoticeText.vue")['default']>
  LazyIeDialog: LazyComponent<typeof import("../../app/components/dialog/IeDialog.vue")['default']>
  LazyMigrateDialog: LazyComponent<typeof import("../../app/components/dialog/MigrateDialog.vue")['default']>
  LazyWordFailedTable: LazyComponent<typeof import("../../app/components/import/WordFailedTable.vue")['default']>
  LazyArticleList: LazyComponent<typeof import("../../app/components/list/ArticleList.vue")['default']>
  LazyBaseList: LazyComponent<typeof import("../../app/components/list/BaseList.vue")['default']>
  LazyDictGroup: LazyComponent<typeof import("../../app/components/list/DictGroup.vue")['default']>
  LazyDictList: LazyComponent<typeof import("../../app/components/list/DictList.vue")['default']>
  LazyList: LazyComponent<typeof import("../../app/components/list/List.vue")['default']>
  LazyWordList: LazyComponent<typeof import("../../app/components/list/WordList.vue")['default']>
  LazyTypingArticleWord: LazyComponent<typeof import("../../app/components/practice-sentences/TypingArticleWord.vue")['default']>
  LazyTypingSentence: LazyComponent<typeof import("../../app/components/practice-sentences/TypingSentence.vue")['default']>
  LazyTypingSentenceItem: LazyComponent<typeof import("../../app/components/practice-sentences/TypingSentenceItem.vue")['default']>
  LazyArticleSetting: LazyComponent<typeof import("../../app/components/setting/ArticleSetting.vue")['default']>
  LazyCommonSetting: LazyComponent<typeof import("../../app/components/setting/CommonSetting.vue")['default']>
  LazyFsrsSetting: LazyComponent<typeof import("../../app/components/setting/FsrsSetting.vue")['default']>
  LazyLog: LazyComponent<typeof import("../../app/components/setting/Log.vue")['default']>
  LazySettingDialog: LazyComponent<typeof import("../../app/components/setting/SettingDialog.vue")['default']>
  LazySettingItem: LazyComponent<typeof import("../../app/components/setting/SettingItem.vue")['default']>
  LazySoundMasterControl: LazyComponent<typeof import("../../app/components/setting/SoundMasterControl.vue")['default']>
  LazySoundSetting: LazyComponent<typeof import("../../app/components/setting/SoundSetting.vue")['default']>
  LazyWordSetting: LazyComponent<typeof import("../../app/components/setting/WordSetting.vue")['default']>
  LazyChangeLastPracticeIndexDialog: LazyComponent<typeof import("../../app/components/word/ChangeLastPracticeIndexDialog.vue")['default']>
  LazyClickableEnglishText: LazyComponent<typeof import("../../app/components/word/ClickableEnglishText.vue")['default']>
  LazyClickableWord: LazyComponent<typeof import("../../app/components/word/ClickableWord.vue")['default']>
  LazyFooter: LazyComponent<typeof import("../../app/components/word/Footer.vue")['default']>
  LazyGroupList: LazyComponent<typeof import("../../app/components/word/GroupList.vue")['default']>
  LazyPracticeOnboardingHost: LazyComponent<typeof import("../../app/components/word/PracticeOnboardingHost.vue")['default']>
  LazyPracticeSettingDialog: LazyComponent<typeof import("../../app/components/word/PracticeSettingDialog.vue")['default']>
  LazyPracticeWordListDialog: LazyComponent<typeof import("../../app/components/word/PracticeWordListDialog.vue")['default']>
  LazyPrevAndNextWord: LazyComponent<typeof import("../../app/components/word/PrevAndNextWord.vue")['default']>
  LazySentenceHightLightWord: LazyComponent<typeof import("../../app/components/word/SentenceHightLightWord.vue")['default']>
  LazyShufflePracticeSettingDialog: LazyComponent<typeof import("../../app/components/word/ShufflePracticeSettingDialog.vue")['default']>
  LazyStatistics: LazyComponent<typeof import("../../app/components/word/Statistics.vue")['default']>
  LazyTranslationList: LazyComponent<typeof import("../../app/components/word/TranslationList.vue")['default']>
  LazyTypeWord: LazyComponent<typeof import("../../app/components/word/TypeWord.vue")['default']>
  LazyVolumeSettingMiniDialog: LazyComponent<typeof import("../../app/components/word/VolumeSettingMiniDialog.vue")['default']>
  LazyWordCollectPopover: LazyComponent<typeof import("../../app/components/word/WordCollectPopover.vue")['default']>
  LazyWordIdentifyPanel: LazyComponent<typeof import("../../app/components/word/WordIdentifyPanel.vue")['default']>
  LazyWordItem: LazyComponent<typeof import("../../app/components/word/WordItem.vue")['default']>
  LazyWordLookupPopover: LazyComponent<typeof import("../../app/components/word/WordLookupPopover.vue")['default']>
  LazyWordMarkPickList: LazyComponent<typeof import("../../app/components/word/WordMarkPickList.vue")['default']>
  LazyWordMetaPanel: LazyComponent<typeof import("../../app/components/word/WordMetaPanel.vue")['default']>
  LazyWordTypingCore: LazyComponent<typeof import("../../app/components/word/WordTypingCore.vue")['default']>
  LazyUnoIcon: LazyComponent<typeof import("../../node_modules/.pnpm/@unocss+nuxt@66.7.5_@unocss_c117d2ce13d61ecf3be709a2b0933c47/node_modules/@unocss/nuxt/runtime/UnoIcon.vue")['default']>
  LazyNuxtWelcome: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/welcome.vue")['default']>
  LazyNuxtLayout: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-layout")['default']>
  LazyNuxtErrorBoundary: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']>
  LazyClientOnly: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/client-only")['default']>
  LazyDevOnly: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/dev-only")['default']>
  LazyServerPlaceholder: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/server-placeholder")['default']>
  LazyNuxtLink: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-link")['default']>
  LazyNuxtLoadingIndicator: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']>
  LazyNuxtTime: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']>
  LazyNuxtRouteAnnouncer: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']>
  LazyNuxtAnnouncer: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-announcer")['default']>
  LazyNuxtImg: LazyComponent<typeof import("../../node_modules/.pnpm/@nuxt+image@2.0.0_@netlify+_247824bac513322053baf33987543c67/node_modules/@nuxt/image/dist/runtime/components/NuxtImg.vue")['default']>
  LazyNuxtPicture: LazyComponent<typeof import("../../node_modules/.pnpm/@nuxt+image@2.0.0_@netlify+_247824bac513322053baf33987543c67/node_modules/@nuxt/image/dist/runtime/components/NuxtPicture.vue")['default']>
  LazyNuxtLinkLocale: LazyComponent<typeof import("../../node_modules/.pnpm/@nuxtjs+i18n@10.2.1_@emnapi_7ce8fc2bbc29d6e7498c4a27e82f17ab/node_modules/@nuxtjs/i18n/dist/runtime/components/NuxtLinkLocale")['default']>
  LazySwitchLocalePathLink: LazyComponent<typeof import("../../node_modules/.pnpm/@nuxtjs+i18n@10.2.1_@emnapi_7ce8fc2bbc29d6e7498c4a27e82f17ab/node_modules/@nuxtjs/i18n/dist/runtime/components/SwitchLocalePathLink")['default']>
  LazyNuxtPage: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/pages/runtime/page")['default']>
  LazyNoScript: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['NoScript']>
  LazyLink: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Link']>
  LazyBase: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Base']>
  LazyTitle: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Title']>
  LazyMeta: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Meta']>
  LazyStyle: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Style']>
  LazyHead: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Head']>
  LazyHtml: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Html']>
  LazyBody: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/head/runtime/components")['Body']>
  LazyNuxtIsland: LazyComponent<typeof import("../../node_modules/.pnpm/nuxt@4.5.2_@babel+plugin-sy_6f825b2af609accb7f329fcfb1a9a593/node_modules/nuxt/dist/app/components/nuxt-island")['default']>
}

declare module 'vue' {
  export interface GlobalComponents extends _GlobalComponents { }
}

export {}
