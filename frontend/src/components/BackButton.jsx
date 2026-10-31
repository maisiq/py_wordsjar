import { useNavigate } from 'react-router-dom';

/**
 * Круглая кнопка «назад» для страниц авторизации: они живут вне Layout,
 * поэтому обычного меню у них нет.
 */
function BackButton({ fallback = '/' }) {
  const navigate = useNavigate();

  const handleClick = () => {
    // idx > 0 — в истории есть предыдущая страница приложения. Если её нет
    // (открыли /login по прямой ссылке), уходим на главную, а не за пределы сайта.
    const canGoBack = window.history.state?.idx > 0;

    if (canGoBack) {
      navigate(-1);
      return;
    }

    navigate(fallback, { replace: true });
  };

  return (
    <button
      type="button"
      className="back-button"
      title="Назад"
      aria-label="Назад"
      onClick={handleClick}
    >
      <svg className="back-button__icon" viewBox="0 0 16 16" aria-hidden="true">
        <path
          d="M13.5 8H3m4-4-4 4 4 4"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </button>
  );
}

export default BackButton;