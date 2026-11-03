/**
 * Перевод ошибок API в понятный пользователю текст.
 *
 * Бэкенд отдаёт технические сообщения («user not found», «internal error»,
 * «word 'x' not found») — их нельзя показывать как есть: они ничего не говорят
 * человеку и раскрывают внутренности сервиса. Здесь одна точка, где сырой ответ
 * превращается в фразу на русском, а оригинал уходит в консоль в dev-режиме.
 */

const DEFAULT_MESSAGE = 'Что-то пошло не так. Попробуйте ещё раз.';

/**
 * Известные сообщения бэкенда (ключи — в нижнем регистре).
 * Для логина «user not found» и «failed to verify password» намеренно дают один
 * и тот же ответ: иначе по тексту ошибки можно перебирать существующие логины.
 */
const DETAIL_MESSAGES = new Map([
  ['user not found', 'Неверное имя пользователя или пароль'],
  ['failed to verify password', 'Неверное имя пользователя или пароль'],
  ['invalid credentials', 'Неверное имя пользователя или пароль'],
  ['user already exists', 'Пользователь с таким именем уже зарегистрирован'],
  ['username already exists', 'Пользователь с таким именем уже зарегистрирован'],
  ['word already exists', 'Такое слово уже есть в словаре'],
  ['word not found', 'Слово не найдено'],
  ['invalid refresh token', 'Сессия истекла, войдите заново'],
  ['invalid or expired token', 'Сессия истекла, войдите заново'],
  ['internal error', 'Ошибка на сервере. Попробуйте позже'],
]);

const STATUS_MESSAGES = new Map([
  [400, 'Проверьте введённые данные'],
  [401, 'Сессия истекла, войдите заново'],
  [403, 'Недостаточно прав для этого действия'],
  [404, 'Не найдено'],
  [409, 'Такая запись уже существует'],
  [422, 'Проверьте введённые данные'],
  [429, 'Слишком много запросов, попробуйте чуть позже'],
  [500, 'Ошибка на сервере. Попробуйте позже'],
  [502, 'Сервер недоступен. Попробуйте позже'],
  [503, 'Сервер недоступен. Попробуйте позже'],
  [504, 'Сервер не ответил вовремя. Попробуйте позже'],
]);

/** Сообщения с подстановками: «word 'cat' not found», «Word with id:7 doesn't exist». */
function matchByPattern(text) {
  if (text.includes('not found') || text.includes("doesn't exist")) {
    return 'Не найдено';
  }
  if (text.includes('already exists')) {
    return 'Такая запись уже существует';
  }
  if (text.includes('token')) {
    return 'Сессия истекла, войдите заново';
  }
  return null;
}

function matchDetail(detail) {
  // 422 от FastAPI присылает массив объектов валидации — это не текст для людей.
  if (typeof detail !== 'string') return null;

  const text = detail.trim().toLowerCase();
  if (!text) return null;

  return DETAIL_MESSAGES.get(text) || matchByPattern(text);
}

/**
 * @param {unknown} error ошибка axios (или что угодно из catch)
 * @param {string} fallback фраза под конкретное действие, если ничего не подошло
 * @returns {string} текст для toast/alert
 */
export function describeError(error, fallback = DEFAULT_MESSAGE) {
  if (!error) return fallback;

  if (import.meta.env.DEV) {
    console.warn('[api]', error?.response?.status, error?.response?.data || error.message || error);
  }

  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
    return 'Сервер не ответил вовремя. Попробуйте ещё раз';
  }

  if (!error.response) {
    // Ошибку без ответа сервера выдаём за проблему связи только если это правда
    // сетевой сбой; программную ошибку маскировать под «нет интернета» нельзя.
    if (error.isAxiosError || error.request) {
      return 'Нет связи с сервером. Проверьте подключение и попробуйте ещё раз';
    }
    return fallback;
  }

  const { status, data } = error.response;
  const detail = typeof data === 'string' ? data : data?.detail;

  return matchDetail(detail) || STATUS_MESSAGES.get(status) || fallback;
}