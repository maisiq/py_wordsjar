import axios from 'axios';
import { createAuthRefreshInterceptor } from 'axios-auth-refresh';

/**
 * По умолчанию API живёт на том же origin, что и приложение:
 * в dev путь проксирует Vite, в проде — nginx. Абсолютный URL нужен только
 * если бэкенд вынесен на отдельный домен (тогда нужен CORS).
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const REQUEST_TIMEOUT = 20_000;

const AUTH_KEY = 'auth';

export function getAuth() {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setAuth(data) {
  if (!data) {
    localStorage.removeItem(AUTH_KEY);
    return;
  }
  localStorage.setItem(AUTH_KEY, JSON.stringify(data));
}

export function clearAuth() {
  localStorage.removeItem(AUTH_KEY);
}

const axiosService = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Без таймаута зависший запрос оставлял бы спиннер навсегда.
  timeout: REQUEST_TIMEOUT,
  withCredentials: true,
});

axiosService.interceptors.request.use((config) => {
  const auth = getAuth();
  if (auth?.access_token) {
    config.headers['X-Auth-Token'] = auth.access_token;
  }
  if (auth?.refresh_token) {
    config.headers['X-Refresh-Token'] = auth.refresh_token;
  }
  return config;
});

const refreshAuthLogic = async (failedRequest) => {
  const auth = getAuth();
  if (!auth?.refresh_token) {
    clearAuth();
    return Promise.reject(failedRequest);
  }

  try {
    const resp = await axios.post(
      `${API_BASE_URL}/refresh`,
      null,
      {
        headers: {
          'X-Refresh-Token': auth.refresh_token,
          'Content-Type': 'application/json',
        },
        timeout: REQUEST_TIMEOUT,
        withCredentials: true,
      },
    );

    const access_token = resp.data.access_token;
    const refresh_token =
      resp.data.refresh_token || resp.data.refres_token || auth.refresh_token;

    setAuth({ access_token, refresh_token });

    failedRequest.response.config.headers['X-Auth-Token'] = access_token;
    if (refresh_token) {
      failedRequest.response.config.headers['X-Refresh-Token'] = refresh_token;
    }

    return Promise.resolve();
  } catch (err) {
    clearAuth();
    return Promise.reject(err);
  }
};

createAuthRefreshInterceptor(axiosService, refreshAuthLogic, {
  statusCodes: [401],
});

export default axiosService;
export { API_BASE_URL };