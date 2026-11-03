import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
// Шрифты лежат в бандле: внешних запросов в рантайме нет (см. CSP в vite.config.js)
import '@fontsource/handjet/cyrillic-700.css';
import '@fontsource/handjet/cyrillic-800.css';
import '@fontsource/handjet/latin-700.css';
import '@fontsource/handjet/latin-800.css';
import '@fontsource/pixelify-sans/latin-700.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/main.css';
import { AuthProvider } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import App from './App';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <App />
          <Toaster
            position="bottom-right"
            toastOptions={{
              duration: 3500,
              style: { minWidth: '300px' },
            }}
          />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </StrictMode>,
);