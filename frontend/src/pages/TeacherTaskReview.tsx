import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';
import CodeReviewViewer from '../components/CodeReviewViewer';
import { useTranslation } from '../store/languageStore';

interface ReviewStudent {
  student_id: number;
  full_name: string;
  username: string;
  group: string;
  has_code_changes: boolean;
}

const TeacherTaskReview: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuthStore();
  const { t } = useTranslation();
  const { id: taskId, studentId } = useParams<{ id: string; studentId: string }>();
  const [review, setReview] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [newComment, setNewComment] = useState<string>('');
  const [newCommentLine, setNewCommentLine] = useState<number>(1);
  const [gradeScore, setGradeScore] = useState<string>('');
  const [gradeComment, setGradeComment] = useState<string>('');
  const [reviewCode, setReviewCode] = useState('');
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'error'>('saved');
  const [students, setStudents] = useState<ReviewStudent[]>([]);

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const progress = await apiFetch(`/admin/tasks/${taskId}/progress`);
        setStudents(progress.students ?? []);
      } catch {
        setStudents([]);
      }
    };
    fetchStudents();
  }, [taskId]);

  useEffect(() => {
    // Ensure the user is a teacher
    if (role !== 'teacher') {
      navigate('/teacher/login', { replace: true });
      return;
    }

    const fetchReview = async (showLoading = true) => {
      try {
        if (showLoading) setLoading(true);
        setError(null);
        const data = await apiFetch(`/admin/tasks/${taskId}/students/${studentId}/review`);
        setReview(data);
        setReviewCode(data.source_code ?? '');
      } catch (err: any) {
        setError(err.message || t('Не удалось загрузить работу', 'Failed to load task review'));
      } finally {
        if (showLoading) setLoading(false);
      }
    };

    fetchReview();
    const interval = window.setInterval(() => fetchReview(false), 3000);
    return () => window.clearInterval(interval);
  }, [navigate, role, taskId, studentId]);

  const switchStudent = (nextStudentId: number) => {
    if (String(nextStudentId) === studentId) return;
    navigate(`/teacher/task/${taskId}/review/${nextStudentId}`);
  };

  const handleAddComment = async (lineNumber = newCommentLine, commentText = newComment) => {
    if (!commentText.trim()) return;
    try {
      // For teachers, we need to specify student_id in query param
      await apiFetch(`/tasks/${taskId}/comments?student_id=${studentId}`, {
        method: 'POST',
        body: JSON.stringify({
          line_number: lineNumber,
          text: commentText
        })
      });
      // Clear the form
      setNewComment('');
      setNewCommentLine(1);
      // Refetch the review to update comments
      const updatedReview = await apiFetch(`/admin/tasks/${taskId}/students/${studentId}/review`);
      setReview(updatedReview);
    } catch (err: any) {
      alert(t('Не удалось добавить комментарий: ', 'Failed to add comment: ') + (err.message || t('Неизвестная ошибка', 'Unknown error')));
    }
  };

  const handleUpdateGrade = async () => {
    if (gradeScore === '') return;
    const score = parseFloat(gradeScore);
    try {
      await apiFetch(`/admin/tasks/${taskId}/grade`, {
        method: 'POST',
        body: JSON.stringify({
          student_id: parseInt(studentId ?? '0', 10),
          score,
          teacher_comment: gradeComment
        })
      });
      // Refetch the review to update grade
      const updatedReview = await apiFetch(`/admin/tasks/${taskId}/students/${studentId}/review`);
      setReview(updatedReview);
      // Clear the grade form? Or keep the values? Let's keep them for now.
    } catch (err: any) {
      alert(t('Не удалось обновить оценку: ', 'Failed to update grade: ') + (err.message || t('Неизвестная ошибка', 'Unknown error')));
    }
  };

  if (loading) return <div className="loading-state">{t('Загружаем работу…', 'Loading review…')}</div>;
  if (error) return <div className="error">{error}</div>;
  if (!review) return <div>{t('Данные работы не найдены', 'Review data not found')}</div>;

  return (
    <div className="teacher-task-review teacher-task-review--with-rail">
      <div className="review-header">
        <div className="page-heading__copy"><span className="eyebrow">{t('Проверка учителем', 'Teacher review')}</span><h2>{t('Проверка задания', 'Task review')}</h2><p className="page-subtitle">{t('Изучите решение, оставьте комментарии и выставьте оценку.', 'Inspect the solution, leave precise feedback and assign a grade.')}</p></div>
        <div className="review-identifiers"><span className="meta-chip">{t('Задание', 'Task')} #{review.task_id}</span><span className="meta-chip">{t('Ученик', 'Student')} #{review.student_id}</span><button className="button-ghost" onClick={() => navigate('/teacher/dashboard')}>{t('← Кабинет', '← Dashboard')}</button></div>
      </div>

      {/* Source Code and Comments Section */}
      {review.source_code !== null && (
        <div className="source-code-section">
          <div className="code-review-heading"><h3>{t('Код ученика', 'Student code')}</h3><span className={`save-indicator save-indicator--${saveStatus}`}>{saveStatus === 'saving' ? t('Сохраняем…', 'Saving…') : saveStatus === 'error' ? t('Ошибка сохранения', 'Save failed') : t('Все изменения сохранены', 'All changes saved')}</span></div>
          <CodeReviewViewer
            key={`task-${taskId}-student-${studentId}`}
            code={reviewCode}
            language={review.language}
            comments={review.comments.map((c: any) => ({
              line_number: c.line_number,
              text: c.text,
              author_type: c.author_type
            }))}
            enableCommenting={true}
            onCommentLineChange={setNewCommentLine}
            onAddComment={handleAddComment}
            readOnly={false}
            collaboration={{
              room: `task-${taskId}-student-${studentId}`,
              user: { name: t('Учитель', 'Teacher'), color: '#a78bfa', colorLight: '#a78bfa33' },
              onStatus: (status) => setSaveStatus(status === 'connected' ? 'saved' : status === 'connecting' ? 'saving' : 'error')
            }}
          />
        </div>
      )}

      {/* Grade Section */}
      <div className="grade-section">
        <div className="grade-summary"><h3>{t('Текущая оценка', 'Current grade')}</h3>{review.grade ? <><span className="grade-summary__score">{review.grade.score ?? '—'}<small>/100</small></span><p>{review.grade.teacher_comment || t('Комментария учителя пока нет.', 'No teacher comment yet.')}</p></> : <><span className="grade-summary__score">—</span><p>{t('Эта работа ещё не оценена.', 'This solution has not been graded yet.')}</p></>}</div>
        <div className="update-grade-form">
          <h4>{t('Изменить оценку', 'Update grade')}</h4>
          <div>
            <label htmlFor="grade-score">{t('Баллы:', 'Score:')}</label>
            <input
              type="number"
              id="grade-score"
              value={gradeScore}
              onChange={(e) => setGradeScore(e.target.value)}
              step="0.01"
              min="0"
              max="100"
            />
          </div>
          <div>
            <label htmlFor="grade-comment">{t('Комментарий:', 'Comment:')}</label>
            <textarea
              id="grade-comment"
              value={gradeComment}
              onChange={(e) => setGradeComment(e.target.value)}
              rows={3}
              placeholder={t('Введите обратную связь для ученика…', 'Enter feedback for the student...')}
            />
          </div>
          <button
            className="button"
            onClick={handleUpdateGrade}
            disabled={gradeScore === ''}
          >
            {t('Сохранить оценку', 'Save grade')}
          </button>
        </div>
      </div>

      {students.length > 0 && (
        <aside className="student-switcher" aria-label={t('Переключить ученика', 'Switch student')}>
          <span className="student-switcher__label">{t('Ученики', 'Students')}</span>
          <div className="student-switcher__list">
            {students.map((student) => {
              const active = String(student.student_id) === studentId;
              return (
                <button
                  type="button"
                  key={student.student_id}
                  className={active ? 'student-switcher__item student-switcher__item--active' : 'student-switcher__item'}
                  onClick={() => switchStudent(student.student_id)}
                  aria-current={active ? 'true' : undefined}
                  aria-label={t(`Открыть работу ${student.full_name}`, `Open ${student.full_name}`)}
                >
                  <span>{(student.username || student.full_name).slice(0, 1).toUpperCase()}</span>
                  {student.has_code_changes && <i aria-label={t('Есть изменения в коде', 'Has code changes')} />}
                  <b className="student-switcher__tooltip"><strong>@{student.username}</strong><small>{student.full_name} · {student.group}</small></b>
                </button>
              );
            })}
          </div>
        </aside>
      )}
    </div>
  );
};

export default TeacherTaskReview;
