import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';
import { useTranslation } from '../store/languageStore';
import LanguagePicker from './LanguagePicker';
import './Layout.css';
import './LayoutAccent.css';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const { role, isAuthenticated, logout } = useAuthStore();
  const { t } = useTranslation();

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
          <span><b>Code</b>Class<small>{t('Учебная среда', 'Learning workspace')}</small></span>
        </NavLink>
        <nav className="app-nav">
          {isAuthenticated && role === 'teacher' && <NavLink to="/teacher/dashboard">{t('Рабочее пространство', 'Workspace')}</NavLink>}
          {isAuthenticated && role === 'teacher' && <NavLink to="/teacher/tests/create">{t('Новая задача', 'New task')}</NavLink>}
          {isAuthenticated && <NavLink className="app-nav__teams" to={role === 'teacher' ? '/teacher/teams' : '/student/teams'}>{t('Команды', 'Teams')}</NavLink>}
          {isAuthenticated && <span className={`role-pill role-pill--${role}`}>{role === 'teacher' ? t('Учитель', 'Teacher') : t('Ученик', 'Student')}</span>}
          <LanguagePicker />
          {isAuthenticated && <button type="button" onClick={handleLogout}>{t('Выйти', 'Log out')}</button>}
        </nav>
      </header>
      <main className="app-main">
        {children}
      </main>
      <footer className="app-footer"><span>CodeClass</span><span>{t('Создано для сосредоточенного обучения', 'Built for focused learning')}</span></footer>
    </div>
  );
};

export default Layout;
