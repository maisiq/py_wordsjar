import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Form, Button } from 'react-bootstrap';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import BackButton from '../components/BackButton';
import { describeError } from '../api/errors';
import { checkPassword, STRENGTH_LABELS } from '../utils/password';

/** Полоски-сегменты индикатора: 1 — слабый, 2 — средний, 3 — надёжный. */
const STRENGTH_SEGMENTS = { weak: 1, medium: 2, strong: 3 };

function PasswordHint({ check }) {
  if (!check.length) return null;

  const filled = STRENGTH_SEGMENTS[check.strength];

  return (
    <div className={`password-hint password-hint--${check.strength}`}>
      <div className="password-hint__bar" aria-hidden="true">
        {[1, 2, 3].map((segment) => (
          <span
            key={segment}
            className={
              segment <= filled
                ? 'password-hint__segment password-hint__segment--on'
                : 'password-hint__segment'
            }
          />
        ))}
      </div>
      <span className="password-hint__label">
        Надёжность пароля: {STRENGTH_LABELS[check.strength]}
      </span>
      {check.problems.length > 0 && (
        <ul className="password-hint__problems">
          {check.problems.map((problem) => (
            <li key={problem}>{problem}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Registration() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [validated, setValidated] = useState(false);
  const [form, setForm] = useState({
    username: '',
    password: '',
    confirm: '',
  });
  const [busy, setBusy] = useState(false);

  const passwordCheck = checkPassword(form.password, {
    username: form.username,
  });

  const handleSubmit = async (event) => {
    event.preventDefault();
    const registrationForm = event.currentTarget;

    if (registrationForm.checkValidity() === false) {
      event.stopPropagation();
      setValidated(true);
      return;
    }

    if (!passwordCheck.ok) {
      toast.error(`Пароль слишком простой: ${passwordCheck.problems.join(', ')}`);
      return;
    }

    if (form.password !== form.confirm) {
      toast.error('Пароли не совпадают');
      return;
    }

    setValidated(true);
    setBusy(true);

    try {
      await register(form.username.trim(), form.password);
      toast.success('Регистрация успешна! Теперь войдите.');
      navigate('/login');
    } catch (err) {
      toast.error(
        describeError(err, 'Не удалось зарегистрироваться. Попробуйте ещё раз'),
      );
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
              Создайте аккаунт, чтобы собирать свою банку слов и проходить
              тесты.
              <br />
              Уже есть аккаунт? <Link to="/login">Войти</Link>
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
            <h5 className="mb-3">Регистрация</h5>
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
                autoComplete="new-password"
                aria-describedby="password-hint"
              />
              <Form.Control.Feedback type="invalid">
                Введите пароль
              </Form.Control.Feedback>
              <div id="password-hint">
                <PasswordHint check={passwordCheck} />
              </div>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Подтверждение пароля</Form.Label>
              <Form.Control
                value={form.confirm}
                onChange={(e) =>
                  setForm({ ...form, confirm: e.target.value })
                }
                required
                type="password"
                placeholder="ещё раз"
                autoComplete="new-password"
              />
              <Form.Control.Feedback type="invalid">
                Подтвердите пароль
              </Form.Control.Feedback>
            </Form.Group>

            <Button
              variant="primary"
              type="submit"
              className="w-100"
              disabled={busy}
            >
              Зарегистрироваться
            </Button>
          </Form>
        </div>
      </div>
    </div>
  );
}

export default Registration;