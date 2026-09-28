import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiFetch } from '../utils/api';
import { useTranslation } from '../store/languageStore';

interface StudentProgress {
  student_id: number;
  full_name: string;
  username: string;
  group: string;
  submission_count: number;
  latest_answer: string | null;
  is_correct: boolean | null;
  comments_count: number;
  has_code_changes: boolean;
  last_code_update: string | null;
  grade: { score: number } | null;
}

interface TaskProgressData {
  task: { id: number; title: string; description?: string; type: 'auto_check' | 'code_review' };
  test?: { id: number; title: string; access_code: string };
  students: StudentProgress[];
}

const TeacherTaskProgress: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const [data, setData] = useState<TaskProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProgress = async (showLoading = true) => {
      try {
        if (showLoading) setLoading(true);
        setData(await apiFetch(`/admin/tasks/${id}/progress`));
      } catch (err: any) {
        setError(err.message || t('Не удалось загрузить прогресс', 'Failed to load task progress'));
      } finally {
        if (showLoading) setLoading(false);
      }
    };
    loadProgress();
    const interval = window.setInterval(() => loadProgress(false), 4000);
    return () => window.clearInterval(interval);
  }, [id]);

  if (loading) return <div className="loading-state">{t('Загружаем прогресс учеников…', 'Loading student progress…')}</div>;
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty-state">{t('Задание не найдено.', 'Task not found.')}</div>;

  const activeCount = data.students.filter((student) => student.submission_count > 0 || student.comments_count > 0 || student.has_code_changes).length;

  return (
    <div className="teacher-task-progress">
      <div className="page-heading">
        <div className="page-heading__copy"><span className="eyebrow">{t('Назначенное задание', 'Assigned task')}</span><h2>{data.task.title}</h2><p className="page-subtitle">{data.task.description || t('Следите за активностью и открывайте работы отдельных учеников.', 'Monitor student activity and open individual reviews.')}</p></div>
        <div className="page-actions"><button className="button-ghost" onClick={() => navigate('/teacher/dashboard')}>{t('← Все задания', '← All tests')}</button></div>
      </div>

      <div className="dashboard-stats"><div className="stat-card"><span>{t('Назначено', 'Enrolled')}</span><b>{data.students.length}</b></div><div className="stat-card"><span>{t('Начали', 'Started')}</span><b>{activeCount}</b></div><div className="stat-card"><span>{t('Тип задания', 'Task type')}</span><b>{data.task.type === 'code_review' ? t('Проверка', 'Review') : t('Авто', 'Auto')}</b></div></div>

      {data.students.length === 0 ? (
        <div className="empty-state"><span className="empty-state__icon">0</span><b>{t('Нет назначенных учеников', 'No students assigned')}</b><p>{t('Измените получателей задания и назначьте группу или отдельного ученика.', 'Edit the task recipients to assign a group or individual student.')}</p></div>
      ) : (
        <div className="progress-table panel">
          <div className="progress-table__head"><span>{t('Ученик', 'Student')}</span><span>{t('Активность', 'Activity')}</span><span>{t('Статус', 'Status')}</span><span>{t('Оценка', 'Grade')}</span><span /></div>
          {data.students.map((student) => {
            const hasActivity = student.submission_count > 0 || student.comments_count > 0 || student.has_code_changes;
            const status = student.is_correct === true ? t('Верно', 'Correct') : student.is_correct === false ? t('Нужна повторная попытка', 'Needs retry') : student.comments_count > 0 || student.has_code_changes ? t('В процессе', 'In progress') : t('Не начато', 'Not started');
            const statusClass = student.is_correct === true ? 'correct' : student.is_correct === false ? 'incorrect' : student.comments_count > 0 || student.has_code_changes ? 'has-comments' : 'not-started';
            return <div className="progress-table__row" key={student.student_id}>
              <div className="student-cell"><span>{student.full_name.slice(0, 1).toUpperCase()}</span><div><b>{student.full_name}</b><small>{student.group}</small></div></div>
              <div className="activity-cell"><span>{student.submission_count} {t('ответов', 'submissions')}</span><span>{student.comments_count} {t('комментариев', 'comments')}</span>{student.has_code_changes && <span>{t('Лайв-код сохранён', 'Live code saved')}</span>}{student.latest_answer && <code title={student.latest_answer}>{student.latest_answer}</code>}</div>
              <span className={`status-badge status-badge--${statusClass}`}>{status}</span>
              <b className="grade-cell">{student.grade ? `${student.grade.score}/100` : '—'}</b>
              <button className="button-secondary" onClick={() => navigate(`/teacher/task/${data.task.id}/review/${student.student_id}`)}>{hasActivity ? t('Открыть работу →', 'Open review →') : t('Открыть ученика →', 'View student →')}</button>
            </div>;
          })}
        </div>
      )}
    </div>
  );
};

export default TeacherTaskProgress;
