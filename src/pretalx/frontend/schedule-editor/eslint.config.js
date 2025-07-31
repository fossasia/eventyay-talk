import vue from 'eslint-plugin-vue'
import vuePug from 'eslint-plugin-vue-pug'
import js from '@eslint/js'

export default [
  // Base JavaScript recommended rules
  js.configs.recommended,
  
  // Vue 3 recommended configuration
  ...vue.configs['flat/recommended'],
  
  // Vue Pug configuration
  {
    plugins: {
      'vue-pug': vuePug
    },
    rules: {
      ...vuePug.configs.recommended.rules
    }
  },
  
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        process: 'readonly',
        // Add other browser globals as needed
      }
    },
    
    rules: {
      // Formatting and style rules
      'arrow-parens': 'off',
      'generator-star-spacing': 'off',
      'indent': ['error', 'tab', { SwitchCase: 1 }],
      'no-tabs': 'off',
      'comma-dangle': 'off',
      'curly': 'off',
      'no-return-assign': 'off',
      'object-curly-spacing': 'off',
      
      // Vue-specific rules
      'vue/require-default-prop': 'off',
      'vue/multi-word-component-names': 'off',
      'vue/max-attributes-per-line': 'off',
      'vue/attribute-hyphenation': ['warn', 'never'],
      'vue/v-on-event-hyphenation': ['warn', 'never'],
      'vue/no-v-html': 'off',
      'vue/require-v-for-key': 'warn',
      'vue/valid-v-for': 'warn',
      'vue/component-api-style': ['error', ['composition', 'options', 'script-setup']],
      'vue/no-undef-properties': 'off',
      'vue/require-explicit-emits': 'off',
      'vue/no-mutating-props': 'error',
      
      // JavaScript rules
      'no-unused-vars': 'warn',
    }
  }
]
