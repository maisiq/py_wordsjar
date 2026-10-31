import { NavLink, useLocation, useNavigate } from 'react-router-dom';

const items = [
  { to: '/', label: 'СЛОВА', end: true },
  { to: '/jar', label: 'БАНКА' },
  { to: '/tests', label: 'ТЕСТ' },
];

function Menu() {
  const navigate = useNavigate();
  const location = useLocation();

  const openAllWords = (e) => {
    e.preventDefault();
    navigate('/', {
      replace: location.pathname === '/',
      state: { resetWords: true },
    });
  };

  return (
    <div className="menu">
      <ul>
        {items.map(({ to, label, end }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={end}
              onClick={to === '/' ? openAllWords : undefined}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
              style={{ color: 'inherit', textDecoration: 'none' }}
            >
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Menu;
