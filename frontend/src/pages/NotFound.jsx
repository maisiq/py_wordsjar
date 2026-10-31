import { Link } from 'react-router-dom';

function NotFound() {
  return (
    <div className="card">
      <div className="card-body text-center py-5">
        <h1 className="display-6 mb-2">404</h1>
        <p className="text-muted mb-4">Такой страницы нет.</p>
        <Link className="btn btn-primary" to="/">
          На главную
        </Link>
      </div>
    </div>
  );
}

export default NotFound;