import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Form, Button } from 'react-bootstrap';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import BackButton from '../components/BackButton';
import { describeError } from '../api/errors';

function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const fromLocation = location.state?.from;
  // Возвращаемся туда, откуда пришли, вместе с query — иначе поиск на главной
  // после входа теряется.
  const from = fromLocation
    ? `${fromLocation.pathname}${fromLocation.search || ''}`
    : '/';

  const [validated, setValidated] = useState(false);
  const [form, setForm] = useState({ username: '', password: '' });
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const loginForm = event.currentTarget;

    if (loginForm.checkValidity() === false) {
      event.stopPropagation();
      setValidated(true);
      return;
    }

    setValidated(true);
    setBusy(true);

    try {
      const info = await login(form.username.trim(), form.password);
      toast.success(
        info?.username ? `Вы вошли как ${info.username}` : 'Успешный вход!',
      );
      navigate(from, { replace: true });
    } catch (err) {
      toast.error(describeError(err, 'Не удалось войти. Попробуйте ещё раз'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container mt-5">
      <BackButton />
      <div className="row justify-content-center">
        <div className="col-md-6 d-flex align-items-center mb-4 mb-md-0">
          <div className="content text-center px-4">
            <h1 className="text-primary">Welcome to WordsJar</h1>
            <p className="content">
              Изучайте слова, собирайте банку и проверяйте себя в тестах.
              <br />
              Нет аккаунта? <Link to="/signup">Регистрация</Link>
            </p>
          </div>
        </div>
        <div className="col-md-6 p-4">
          <Form
            className="border p-4 rounded bg-white"
            noValidate
            validated={validated}
            onSubmit={handleSubmit}
          >
            <h5 className="mb-3">Вход</h5>
            <Form.Group className="mb-3">
              <Form.Label>Имя пользователя</Form.Label>
              <Form.Control
                value={form.username}
                onChange={(e) =>
                  setForm({ ...form, username: e.target.value })
                }
                required
                type="text"
                placeholder="username"
                autoComplete="username"
              />
              <Form.Control.Feedback type="invalid">
                Введите имя пользователя
              </Form.Control.Feedback>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Пароль</Form.Label>
              <Form.Control
                value={form.password}
                onChange={(e) =>
                  setForm({ ...form, password: e.target.value })
                }
                required
                type="password"
                placeholder="пароль"
                autoComplete="current-password"
              />
              <Form.Control.Feedback type="invalid">
                Введите пароль
              </Form.Control.Feedback>
            </Form.Group>

            <Button
              variant="primary"
              type="submit"
              className="w-100"
              disabled={busy}
            >
              Войти
            </Button>
          </Form>
        </div>
      </div>
    </div>
  );
}

export default Login;
