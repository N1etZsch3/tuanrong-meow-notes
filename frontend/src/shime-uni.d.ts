export {}

declare module "vue" {
  type Hooks = App.AppInstance & Page.PageInstance;
  interface ComponentCustomOptions extends Hooks {}
}

declare module "@vue/runtime-core" {
  interface ComponentCustomProperties {
    drawer: {
      init: (...args: unknown[]) => void;
      tap: (...args: unknown[]) => void;
      touchstart: (...args: unknown[]) => void;
      touchmove: (...args: unknown[]) => void;
      touchend: (...args: unknown[]) => void;
    };
    filterAnim: {
      onMenuStateChange: (...args: unknown[]) => void;
    };
  }
}
