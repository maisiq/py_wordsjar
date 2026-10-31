import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './routes/ProtectedRoute';
import Home from './pages/Home';
import Jar from './pages/Jar';
import Login from './pages/Login';
import Registration from './pages/Registration';
import NotFound from './pages/NotFound';

// Тест грузится отдельным чанком: на главной и в банке он не нужен.
const Exam = lazy(() => import('./pages/Exam'));

function PageFallback() {
  return (
    <div className="text-center py-5">
      <div className="spinner-border text-primary" role="status">
        <span className="visually-hidden">Загрузка...</span>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="app-shell">
      <main className="app-main">
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Home />} />
              <Route
                path="/jar"
                element={
                  <ProtectedRoute>
                    <Jar />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/tests"
                element={
                  <ProtectedRoute>
                    <Exam />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<NotFound />} />
            </Route>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Registration />} />
          </Routes>
        </Suspense>
      </main>

      <footer className="site-footer">
        <span>© 2026 </span>
        <a
          href="https://github.com/maisiq"
          target="_blank"
          rel="noopener noreferrer"
        >
          maisiq
        </a>
      </footer>
    </div>
  );
}

export default App;