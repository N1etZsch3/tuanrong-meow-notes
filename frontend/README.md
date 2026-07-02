# Frontend

uni-app frontend for the Campus Cat Association Map Task System WeChat Mini Program.

Planned stack:

- uni-app
- Vue 3
- TypeScript
- Pinia
- uView Plus or lightweight custom components
- Amap/Gaode Map SDK

Read `../AGENTS.md` and the relevant documents under `../docs` before adding frontend code.

## Scripts

- `npm run dev`: run the WeChat Mini Program dev build.
- `npm run build`: build the WeChat Mini Program output.
- `npm run dev:h5`: run the H5 dev server for browser debugging.
- `npm run test`: run frontend unit tests.
- `npm run type-check`: run TypeScript checks.

## API Environment

Local development can omit `VITE_API_BASE_URL` and falls back to
`http://localhost:8000/api/v1`.

WeChat Mini Program production builds must configure a real HTTPS API domain,
otherwise the build fails instead of silently packaging a localhost request URL.
Create an ignored `frontend/.env.production` file or set the environment
variable in CI:

```text
VITE_API_BASE_URL=https://your-api-domain.example.com/api/v1
```

## Source Layout

See `src/README.md` before adding frontend source files.
