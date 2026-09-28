import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';
import { useTranslation } from '../store/languageStore';

interface StudentLoginCredentials {
  username: string;
  password: string;
}

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const { t } = useTranslation();
  const [credentials, setCredentials] = useState<StudentLoginCredentials>({
    username: '',
    password: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch('/auth/student-login', {
        method: 'POST',
        body: JSON.stringify(credentials)
      });
      login('student');
      navigate(result.needs_group ? '/student/group' : '/test');
    } catch (err: any) {
      setError(err.message || t('Не удалось войти', 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <span className="login-page__eyebrow">{t('Защищённый вход', 'Secure access')}</span>
      <h2>{t('Вход для ученика', 'Student Login')}</h2>
      <p className="page-subtitle">{t('Войдите в свою учётную запись.', 'Sign in with your student account.')}</p>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">{t('Логин:', 'Username:')}</label>
          <input
            type="text"
            id="username"
            name="username"
            value={credentials.username}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label htmlFor="password">{t('Пароль:', 'Password:')}</label>
          <input
            type="password"
            id="password"
            name="password"
            value={credentials.password}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? t('Входим…', 'Logging in...') : t('Войти', 'Login')}
        </button>
      </form>
      <p className="login-switch">{t('Нет аккаунта?', 'No account?')} <Link to="/register">{t('Зарегистрироваться', 'Create one')}</Link><br />{t('Вы учитель?', 'Are you a teacher?')} <Link to="/teacher/login">{t('Вход для учителя', 'Teacher sign in')}</Link></p>
    </div>
  );
};

export default Login;
