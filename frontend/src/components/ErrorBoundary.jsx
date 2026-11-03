import { Component } from 'react';

/**
 * Ловит ошибки отрисовки, чтобы вместо белого экрана пользователь увидел
 * понятное сообщение и кнопку перезагрузки. Ошибки обработчиков событий и
 * асинхронного кода сюда не попадают — их показывают toast'ы в местах запросов.
 */
class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('Unhandled UI error', error, info);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    const { error } = this.state;

    if (!error) {
      return this.props.children;
    }

    return (
      <div className="container py-5">
        <div className="card mx-auto" style={{ maxWidth: '560px' }}>
          <div className="card-body text-center py-5">
            <h1 className="h4 mb-3">Что-то пошло не так</h1>
            <p className="text-muted">
              Страница не смогла отрисоваться. Попробуйте перезагрузить — данные
              на сервере не потеряны.
            </p>
            {import.meta.env.DEV && (
              <pre className="text-start small bg-light p-3 rounded-3 overflow-auto">
                {String(error.stack || error)}
              </pre>
            )}
            <button
              type="button"
              className="btn btn-primary"
              onClick={this.handleReload}
            >
              Перезагрузить
            </button>
          </div>
        </div>
      </div>
    );
  }
}

export default ErrorBoundary;