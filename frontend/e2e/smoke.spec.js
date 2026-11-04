import { test, expect } from '@playwright/test';

test.describe('smoke', () => {
  test('главная: каркас приложения', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveTitle(/Words Jar/i);

    await expect(page.getByRole('link', { name: 'wordsJar' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'СЛОВА' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'БАНКА' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'ТЕСТ' })).toBeVisible();

    await expect(
      page.getByRole('textbox', { name: 'Поиск слов' }),
    ).toBeVisible();
    await expect(page.getByRole('button', { name: 'Войти' })).toBeVisible();

    await expect(page.locator('footer.site-footer')).toContainText('maisiq');
  });

  test('страница входа', async ({ page }) => {
    await page.goto('/login');

    await expect(
      page.getByRole('heading', { name: 'Welcome to WordsJar' }),
    ).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Вход' })).toBeVisible();
    await expect(page.getByLabel('Имя пользователя')).toBeVisible();
    await expect(page.getByLabel('Пароль')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Войти' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Регистрация' })).toBeVisible();
  });

  test('страница регистрации', async ({ page }) => {
    await page.goto('/signup');

    await expect(
      page.getByRole('heading', { name: 'Welcome to WordsJar' }),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Регистрация' }),
    ).toBeVisible();
    await expect(page.getByLabel('Имя пользователя')).toBeVisible();
    await expect(page.getByLabel('Пароль', { exact: true })).toBeVisible();
    await expect(page.getByLabel('Подтверждение пароля')).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Зарегистрироваться' }),
    ).toBeVisible();
    await expect(page.getByRole('link', { name: 'Войти' })).toBeVisible();
  });

  test('гость с /jar уходит на /login', async ({ page }) => {
    await page.goto('/jar');
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole('heading', { name: 'Вход' })).toBeVisible();
  });

  test('гость с /tests уходит на /login', async ({ page }) => {
    await page.goto('/tests');
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole('heading', { name: 'Вход' })).toBeVisible();
  });

  test('404', async ({ page }) => {
    await page.goto('/this-page-does-not-exist');

    await expect(page.getByRole('heading', { name: '404' })).toBeVisible();
    await expect(page.getByText('Такой страницы нет.')).toBeVisible();

    await page.getByRole('link', { name: 'На главную' }).click();
    await expect(page).toHaveURL('/');
  });

  test('кнопка «Войти» с главной ведёт на /login', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Войти' }).click();
    await expect(page).toHaveURL(/\/login$/);
  });
});
