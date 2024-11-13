/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly APP_NAME: string;
  readonly BACKEND_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
