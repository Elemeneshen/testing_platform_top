import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';
import './Layout.css';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const { role, isAuthenticated, logout } = useAuthStore();

  const handleLogout = async () => {
    try { await apiFetch('/auth/logout', { method: 'POST' }); } finally {
      logout();
      navigate(role === 'teacher' ? '/teacher/login' : '/login');
    }
  };

  return (
    <div className="app-layout">
      <header className="app-header">
        <NavLink className="app-brand" to={role === 'teacher' ? '/teacher/dashboard' : role === 'student' ? '/test' : '/login'}>
          <span className="app-brand__mark">{'</>'}</span>
          <span><b>Code</b>Class<small>Learning workspace</small></span>
        </NavLink>
        {isAuthenticated && <nav className="app-nav">
          {role === 'teacher' && <NavLink to="/teacher/dashboard">Workspace</NavLink>}
          {role === 'teacher' && <NavLink to="/teacher/tests/create">New test</NavLink>}
          <span className={`role-pill role-pill--${role}`}>{role}</span>
          <button type="button" onClick={handleLogout}>Log out</button>
        </nav>}
      </header>
      <main className="app-main">
        {children}
      </main>
      <footer className="app-footer"><span>CodeClass</span><span>Built for focused learning</span></footer>
    </div>
  );
};

export default Layout;
