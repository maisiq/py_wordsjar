import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Сборка с локальным адресом API бессмысленна: в браузере пользователя
// localhost — это его собственный компьютер.
const LOCAL_API_URL = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i;

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');

  // process.env учитывается, чтобы значение приходило build-arg'ом из Docker.
  const apiBaseUrl =
    process.env.VITE_API_BASE_URL || env.VITE_API_BASE_URL || '/api/v1';
  const devProxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://localhost:8080';

  if (command === 'build' && LOCAL_API_URL.test(apiBaseUrl)) {
    throw new Error(
      `VITE_API_BASE_URL="${apiBaseUrl}" указывает на локальный адрес. ` +
        'Для продакшен-сборки оставьте /api/v1 (запросы пойдут на тот же ' +
        'домен) или укажите публичный URL API.',
    );
  }

  return {
    plugins: [react()],
    server: {
      host: 'frontend.local.test',
      port: 3000,
      // В dev роль продового nginx: тот же origin, без CORS.
      proxy: {
        '/api/v1': {
          target: devProxyTarget,
          changeOrigin: true,
        },
      },
    },
    // CSP и остальные заголовки безопасности отдаёт nginx:
    // frontend/docker/security-headers.conf
  };
});