import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ThemePicker from '../components/ThemePicker';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';
import { useTranslation } from '../store/languageStore';

// Helper function to get task status
const getTaskStatus = (task: any) => {
  // Check if there's a correct submission
  const hasCorrectSubmission = task.submissions?.some((sub: any) => sub.is_correct === true);
  if (hasCorrectSubmission) return 'correct';

  // Check if there's any submission (incorrect)
  const hasAnySubmission = task.submissions?.some((sub: any) => sub.is_correct !== null);
  if (hasAnySubmission) return 'incorrect';

  // Check if there are comments (student or teacher)
  const hasComments = task.code_comments?.length > 0;
  if (hasComments) return 'has-comments';

  // Default status
  return 'not-started';
};

// Status label mapping
const getStatusLabel = (status: string, t: (ru: string, en: string) => string) => {
  switch (status) {
    case 'not-started': return t('Не начато', 'Not started');
    case 'correct': return t('Решено верно', 'Correctly submitted');
    case 'incorrect': return t('Есть ошибка', 'Incorrectly submitted');
    case 'has-comments': return t('Есть комментарии', 'Has comments');
    default: return t('Неизвестно', 'Unknown');
  }
};

const Test: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuthStore();
  const { t } = useTranslation();
  const [test, setTest] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Ensure the user is a student
    if (role !== 'student') {
      navigate('/login', { replace: true });
      return;
    }

    const fetchTest = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiFetch('/tasks');
        setTest(data);
      } catch (err: any) {
        setError(err.message || t('Не удалось загрузить задания', 'Failed to load test'));
      } finally {
        setLoading(false);
      }
    };

    fetchTest();
  }, [navigate, role]);

  if (loading) return <div className="loading-state">{t('Загружаем задания…', 'Loading test…')}</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="test-page">
      <div className="page-heading"><div className="page-heading__copy"><span className="eyebrow">{t('Рабочее пространство ученика', 'Student workspace')}</span><h2>{t('Ваши задания', 'Your tasks')}</h2><p className="page-subtitle">{t('Здесь показаны задания, опубликованные для вас или вашей группы.', 'Only assignments published for you or your group appear here.')}</p></div><div className="task-meta"><span className="meta-chip">{test.length} {t('заданий', 'tasks')}</span></div></div>
      <ThemePicker compact audience="student" />
      {test.length === 0 ? <div className="empty-state"><span className="empty-state__icon">0</span><b>{t('Нет активных заданий', 'No active tasks')}</b><p>{t('Учитель пока не опубликовал для вас задания.', 'Your teacher has not published any assignments for you yet.')}</p></div> : <ul className="resource-list">
        {test.map((task: any, index: number) => {
          const status = getTaskStatus(task);
          const statusLabel = getStatusLabel(status, t);

          return (
            <li className="resource-card" key={task.id}><div className="resource-card__main"><span className="resource-card__index">{String(index + 1).padStart(2, '0')}</span><div className="resource-card__copy"><b>{task.title}</b><span>{task.type === 'code_review' ? t('Проверка кода', 'Code review') : t('Автопроверка', 'Auto-check')}</span></div></div><div className="resource-card__side"><span className={`status-badge status-badge--${status}`}>{statusLabel}</span><button className="button-secondary" onClick={() => navigate(`/task/${task.id}`)}>{t('Открыть задание →', 'Open task →')}</button></div></li>
          );
        })}
      </ul>}
    </div>
  );
};

export default Test;
