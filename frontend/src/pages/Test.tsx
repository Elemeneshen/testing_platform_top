import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';

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
const getStatusLabel = (status: string) => {
  switch (status) {
    case 'not-started': return 'Not started';
    case 'correct': return 'Correctly submitted';
    case 'incorrect': return 'Incorrectly submitted';
    case 'has-comments': return 'Has comments';
    default: return 'Unknown';
  }
};

const Test: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuthStore();
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
        setError(err.message || 'Failed to load test');
      } finally {
        setLoading(false);
      }
    };

    fetchTest();
  }, [navigate, role]);

  if (loading) return <div className="loading-state">Loading test…</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="test-page">
      <div className="page-heading"><div className="page-heading__copy"><span className="eyebrow">Student workspace</span><h2>Your tasks</h2><p className="page-subtitle">Only assignments published for you or your group appear here.</p></div><div className="task-meta"><span className="meta-chip">{test.length} tasks</span></div></div>
      {test.length === 0 ? <div className="empty-state"><span className="empty-state__icon">0</span><b>No active tasks</b><p>Your teacher has not published any assignments for you yet.</p></div> : <ul className="resource-list">
        {test.map((task: any, index: number) => {
          const status = getTaskStatus(task);
          const statusLabel = getStatusLabel(status);

          return (
            <li className="resource-card" key={task.id}><div className="resource-card__main"><span className="resource-card__index">{String(index + 1).padStart(2, '0')}</span><div className="resource-card__copy"><b>{task.title}</b><span>{task.type === 'code_review' ? 'Code review' : 'Auto-check'} task</span></div></div><div className="resource-card__side"><span className={`status-badge status-badge--${status}`}>{statusLabel}</span><button className="button-secondary" onClick={() => navigate(`/task/${task.id}`)}>Open task →</button></div></li>
          );
        })}
      </ul>}
    </div>
  );
};

export default Test;
