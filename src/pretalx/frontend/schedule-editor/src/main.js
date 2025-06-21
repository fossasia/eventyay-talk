import { createApp } from 'vue'
import Buntpapier from 'buntpapier'

import App from './App.vue'
import '~/styles/global.styl'
import i18n from '~/lib/i18n'

const app = createApp(App, {
	locale: 'en-ie'
})
app.use(Buntpapier)
const lang = document.querySelector("#app").dataset.gettext;
(async () => {
    try {
        const i18nPlugin = await i18n(lang);
        app.use(i18nPlugin);
        app.mount('#app');
    } catch (error) {
        console.error('Application initialization failed:', error);
    }
})();