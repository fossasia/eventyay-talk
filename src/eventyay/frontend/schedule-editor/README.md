# eventyay-schedule-editor

## Project setup
```
npm ci
```

### Compiles and hot-reloads for development
```
npm start
```

### Compiles and minifies for production
```
npm run build
```

### Build for eventyay (web component)
```
npm run build:wc
```

Then copy ``dist/*js`` to ``src/eventyay/static/orga/js/`` in eventyay.

### Release library to npm

```sh
npm version minor|patch
npm publish --access=public
```

### Lints and fixes files
```
npm run lint
```
