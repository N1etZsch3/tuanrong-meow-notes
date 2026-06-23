export {};

declare global {
  interface Window {
    AMap?: any;
    _AMapSecurityConfig?: {
      securityJsCode: string;
    };
    __initCampusCatMap?: () => void;
  }
}
