# --- Этап сборки -------------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

# Зависимости отдельным слоем: правка исходников не переустанавливает пакеты
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# По умолчанию API на том же origin (/api/v1), проксирует его nginx ниже.
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# --- Этап раздачи ------------------------------------------------------------
FROM nginx:alpine

# В официальном образе каталога для сниппетов нет
RUN mkdir -p /etc/nginx/snippets

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# busybox-wget: -q тихо, -O /dev/null выбрасывает тело ответа
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]