import { createApp } from 'vue'
import App from './App.vue'
import Vue3YouTube from 'vue3-youtube'

const app = createApp(App)
app.use(Vue3YouTube)
app.mount('#app')