// Plugins
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import Fonts from 'unplugin-fonts/vite'
import Layouts from 'vite-plugin-vue-layouts'
import Vue from '@vitejs/plugin-vue'
import VueRouter from 'unplugin-vue-router/vite'
import Vuetify, {transformAssetUrls} from 'vite-plugin-vuetify'

// Utilities
import {defineConfig} from 'vite'
import {fileURLToPath, URL} from 'node:url'


// Config
import * as config from 'config';
const definedData = {
    'import.meta.env.APP_NAME': JSON.stringify(config.get('APP_NAME')),
    'import.meta.env.BACKEND_URL': JSON.stringify(config.get('BACKEND_URL')),
};


// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        VueRouter({
            dts: 'src/typed-router.d.ts',
        }),
        Layouts(),
        AutoImport({
            imports: [
                'vue',
                {
                    'vue-router/auto': ['useRoute', 'useRouter'],
                }
            ],
            dts: 'src/auto-imports.d.ts',
            eslintrc: {
                enabled: true,
            },
            vueTemplate: true,
        }),
        Components({
            dts: 'src/components.d.ts',
        }),
        Vue({
            template: {transformAssetUrls},
        }),
        // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
        Vuetify({
            autoImport: true,
            styles: {
                configFile: 'src/styles/settings.scss',
            },
        }),
        Fonts({
            google: {
                families: [{
                    name: 'Roboto',
                    styles: 'wght@100;300;400;500;700;900',
                }],
            },
        }),
    ],
    define: {'process.env': {}, ...definedData},
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        },
        extensions: [
            '.js',
            '.json',
            '.jsx',
            '.mjs',
            '.ts',
            '.tsx',
            '.vue',
        ],
    },
    server: {
        host: true,
        port: 8080,
        watch: {
            usePolling: true,
        },
    },
})
