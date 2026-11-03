import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

function Layout() {
  return (
    <div className="container mt-4 app-container">
      <Sidebar />
      <div className="page-content">
        <Outlet />
      </div>
      <div className="sidebar sidebar--right" aria-hidden="true" />
    </div>
  );
}

export default Layout;