import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'cc.typewords.lite',
  appName: 'Type Words',
  webDir: 'www',
  android: {
    allowMixedContent: false,
  },
  server: {
    androidScheme: 'https',
  },
}

export default config
