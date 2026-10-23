import { createRoot } from 'react-dom/client';
import './styles.css';
import App from './App.jsx';
import { ErrorBoundary } from './components/ErrorBoundary.jsx';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);
