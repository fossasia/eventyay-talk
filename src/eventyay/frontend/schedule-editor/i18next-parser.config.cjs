const VueLexer = require('./i18next-parser-vue-lexer.cjs')

// Used via the eventyay makemessages command

module.exports = {
  locales: ['en'],
  lexers: {
    vue: [VueLexer]
  }
}
