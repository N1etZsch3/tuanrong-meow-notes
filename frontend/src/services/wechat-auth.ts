export type WechatLoginCode = string | null;

export function requestWechatLoginCode(): Promise<WechatLoginCode> {
  if (typeof uni === "undefined" || typeof uni.login !== "function") {
    return Promise.resolve(null);
  }

  return new Promise((resolve) => {
    try {
      uni.login({
        provider: "weixin",
        success: (result) => {
          const code = typeof result.code === "string" ? result.code.trim() : "";
          resolve(code || null);
        },
        fail: () => resolve(null),
      });
    } catch {
      resolve(null);
    }
  });
}
