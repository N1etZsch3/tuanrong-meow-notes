/// <reference types="vite/client" />

declare module '*.vue' {
  import { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module "*.wxs" {
  const content: any;
  export default content;
}

declare module "*.wxs.js" {
  const content: any;
  export default content;
}
