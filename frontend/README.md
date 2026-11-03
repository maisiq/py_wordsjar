# Words Jar — фронтенд

SPA на React 19 + Vite 8, стили — Bootstrap 5 через react-bootstrap.
Общается с API Words Jar (`/api/v1`), исходники бэкенда лежат в `../backend`.

## Требования

- Node.js `^20.19.0` или `>=22.12.0` (см. `engines` и `.nvmrc`), npm 11.
- Запущенный бэкенд на `http://localhost:8080` для работы с данными.

## Быстрый старт

```bash
npm ci                  # или npm install
cp .env.example .env    # один раз, значения по умолчанию подходят для dev
npm run dev
```

Приложение поднимется на `http://frontend.local.test:3000` — этот хост прописан
в `server.host` в `vite.config.js`, поэтому в `hosts` нужна соответствующая
запись (`127.0.0.1 frontend.local.test`).

## Скрипты

| Скрипт | Что делает |
| --- | --- |
| `npm run dev` | Дев-сервер с HMR |
| `npm run build` | Продакшен-сборка в `dist/` |
| `npm run preview` | Локальный просмотр собранного `dist/` |
| `npm run lint` | oxlint по `src/` (и по остальным файлам) |

## Переменные окружения

Значения читаются на этапе сборки и **вшиваются в бандл** — секретов здесь быть
не может.

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api/v1` | Базовый URL API |
| `VITE_DEV_PROXY_TARGET` | `http://localhost:8080` | Куда Vite проксирует `/api/v1` в dev |

По умолчанию API запрашивается с того же origin, поэтому CORS не участвует:

- в разработке `/api/v1` проксирует Vite (`server.proxy` в `vite.config.js`);
- в продакшене тот же путь должен проксировать nginx на контейнер бэкенда.

Абсолютный URL (`https://api.example.com/api/v1`) нужен только если API живёт
на отдельном домене — тогда на бэкенде надо разрешить этот origin в CORS.

Сборка с `VITE_API_BASE_URL`, указывающим на `localhost`/`127.0.0.1`,
намеренно падает: такой адрес в браузере пользователя означает его собственный
компьютер.

## Структура

```
src/
  api/axios.js          клиент API, токены, авто-refresh по 401
  components/           переиспользуемые компоненты (карточка слова, пагинация, ...)
  context/AuthContext   состояние авторизации
  hooks/                useCursorPagination, useDeleteWord
  pages/                Home, Jar, Exam, Login, Registration, NotFound
  routes/ProtectedRoute защита приватных страниц
  styles/main.css       все стили поверх Bootstrap
```

## Особенности

- **Пагинация курсорная.** `useCursorPagination` хранит курсоры страниц и
  игнорирует ответы устаревших запросов, поэтому быстрое переключение
  страниц/сортировок не перезаписывает список.
- **Сортировка банки** — `SortDropdown` в шапке страницы `/jar`, варианты
  отправляются в API как `order_by` + `desc`. Вторым ключом везде идёт `id`,
  иначе при одинаковом `rating` курсор нестабилен.
- **Шрифты локальные** (`@fontsource`), внешних запросов в рантайме нет —
  из-за этого возможна строгая CSP.
- **Заголовки безопасности и CSP** отдаёт nginx
  (`docker/security-headers.conf`), в dev-режиме их нет.
- **Токены** хранятся в `localStorage` (`auth`), передаются заголовками
  `X-Auth-Token` / `X-Refresh-Token`.

## Деплой

Образ собирается из этого каталога и раздаёт статику через nginx:

```bash
docker compose up -d --build frontend
```

Что делает nginx ([docker/nginx.conf](docker/nginx.conf)):

- `try_files ... /index.html` — SPA-fallback, поэтому прямые ссылки на `/jar`,
  `/tests` и клиентская 404-страница работают;
- `/api/v1/` проксируется на бэкенд: фронтенд и API живут на одном origin;
- `/assets/*` кэшируется навсегда (в именах есть хэш), `index.html` — без кэша;
- gzip, security-заголовки и CSP ([docker/security-headers.conf](docker/security-headers.conf));
- `/healthz` — для HEALTHCHECK контейнера.

Бэкенд в корневом `docker-compose.yml` работает в `network_mode: host`, поэтому
nginx обращается к нему через `host.docker.internal:8080`. Когда бэкенд переедет
в сеть compose, в `docker/nginx.conf` нужно заменить адрес на
`http://backend:8080`.

API на другом домене задаётся на этапе сборки:

```bash
docker build --build-arg VITE_API_BASE_URL=https://api.example.com/api/v1 .
```

Порт по умолчанию — 80, меняется в `ports` сервиса `frontend`.

## Что ещё не сделано

- Тесты (Vitest + Testing Library, Playwright для smoke) и CI.