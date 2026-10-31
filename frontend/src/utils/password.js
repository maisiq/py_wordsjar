/**
 * Проверка сложности пароля на клиенте.
 *
 * Требование — «средняя сложность»: не короче 8 символов и минимум два вида
 * символов. Верхнюю планку (12+, три вида, обязательные спецсимволы) сознательно
 * не поднимаем, чтобы не вынуждать людей записывать пароль на бумажке.
 */

export const MIN_PASSWORD_LENGTH = 8;

/** Самые частые пароли: их проверяют первыми при подборе. */
const COMMON_PASSWORDS = new Set([
  'password',
  'password1',
  'password123',
  'qwerty12',
  'qwerty123',
  'qwerty1234',
  '12345678',
  '123456789',
  '1234567890',
  'iloveyou',
  'admin123',
  'letmein1',
  'welcome1',
  '1q2w3e4r',
]);

const CHARACTER_CLASSES = [
  /[a-zа-яё]/,
  /[A-ZА-ЯЁ]/,
  /\d/,
  /[^\p{L}\p{N}]/u,
];

/**
 * @param {string} password
 * @param {{ username?: string }} [options]
 * @returns {{ ok: boolean, strength: 'weak'|'medium'|'strong', problems: string[], length: number }}
 */
export function checkPassword(password, { username = '' } = {}) {
  const value = String(password ?? '');
  const classes = CHARACTER_CLASSES.filter((re) => re.test(value)).length;
  const problems = [];

  if (value.length < MIN_PASSWORD_LENGTH) {
    problems.push(`не короче ${MIN_PASSWORD_LENGTH} символов`);
  }
  if (classes < 2) {
    problems.push(
      'минимум два вида символов: строчные и заглавные буквы, цифры, знаки',
    );
  }
  if (value.length > 0 && /^(.)\1+$/u.test(value)) {
    problems.push('не из одного повторяющегося символа');
  }
  if (value.length > 0 && COMMON_PASSWORDS.has(value.toLowerCase())) {
    problems.push('не из списка самых частых паролей');
  }
  if (
    value.length > 0 &&
    username &&
    value.toLowerCase() === username.trim().toLowerCase()
  ) {
    problems.push('не совпадать с именем пользователя');
  }

  const ok = value.length > 0 && problems.length === 0;
  const strength = !ok
    ? 'weak'
    : value.length >= 12 && classes >= 3
      ? 'strong'
      : 'medium';

  return { ok, strength, problems, length: value.length };
}

export const STRENGTH_LABELS = {
  weak: 'слабый',
  medium: 'средний',
  strong: 'надёжный',
};