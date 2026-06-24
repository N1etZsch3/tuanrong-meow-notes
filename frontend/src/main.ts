import { createSSRApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { redirectToLogin, setAuthExpiredHandler } from "@/services/auth-session";
import { useUserStore } from "@/stores/user";

export function createApp() {
  const app = createSSRApp(App);
  const pinia = createPinia();

  app.use(pinia);
  setAuthExpiredHandler(() => {
    useUserStore(pinia).clearSession();
    redirectToLogin();
  });

  return {
    app,
  };
}
