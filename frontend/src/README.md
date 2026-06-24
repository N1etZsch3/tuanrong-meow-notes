# Frontend Source Layout

Use this layout for frontend code:

- `api`: module-level API functions, grouped by business domain.
- `components`: reusable visual components.
- `composables`: reusable Vue composition functions.
- `config`: environment and app configuration.
- `constants`: shared constants such as storage keys.
- `pages`: uni-app pages registered in `pages.json`.
- `services`: cross-module infrastructure such as request wrappers.
- `stores`: Pinia stores.
- `styles`: shared style tokens and mixins.
- `types`: shared TypeScript types that mirror backend `snake_case` fields.

Assets, prototypes, and prototype code live outside `src`:

- `../素材`
- `../页面原型`
- `../页面原型代码`

Before building a page, inspect the matching image in `../页面原型` and use assets from `../素材`. If a required asset is missing, use an explicit placeholder and record it in the handoff.
