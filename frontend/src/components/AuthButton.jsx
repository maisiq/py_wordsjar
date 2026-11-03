import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { describeError } from '../api/errors';
import toast from 'react-hot-toast';

function LogoutIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M10 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4" />
      <path d="M10 17l5-5-5-5" />
      <path d="M15 12H9" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg
      className="auth-icon"
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      fill="currentColor"
      viewBox="0 0 16 16"
    >
      <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3Zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
    </svg>
  );
}

function AuthButton() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);

  const handleClick = async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    setBusy(true);
    try {
      await logout();
      toast.success('Выход выполнен успешно');
      navigate('/');
    } catch (err) {
      toast.error(describeError(err, 'Не удалось выйти. Попробуйте ещё раз'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <button
      className="btn btn-sm btn-outline-primary ms-2 flex-shrink-0"
      type="button"
      onClick={handleClick}
      disabled={busy}
      aria-label={isAuthenticated ? 'Выйти' : 'Войти'}
    >
      {isAuthenticated ? <LogoutIcon /> : <UserIcon />}
    </button>
  );
}

export default AuthButton;
