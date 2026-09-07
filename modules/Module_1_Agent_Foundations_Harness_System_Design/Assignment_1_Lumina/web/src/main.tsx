import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { EvalsPage } from './EvalsPage';
import './styles.css';

/**
 * Two routes, no router dependency: / is the product and /evals is the evidence page a
 * grader opens. Both must survive a hard refresh, which is what web/vercel.json's
 * rewrite is for.
 */
const path = window.location.pathname.replace(/\/+$/, '');
const route = path === '/evals' ? 'evals' : 'app';

createRoot(document.getElementById('root')!).render(
  <StrictMode>{route === 'evals' ? <EvalsPage /> : <App route="app" />}</StrictMode>
);
