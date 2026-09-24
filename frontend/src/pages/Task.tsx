import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';
import CodeReviewViewer from '../components/CodeReviewViewer';

const Task: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuthStore();
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string>('');
  const [submissionResult, setSubmissionResult] = useState<{ correct: boolean; message: string } | null>(null);
  // For code_review task comments
  const [newComment, setNewComment] = useState<string>('');
  const [newCommentLine, setNewCommentLine] = useState<number>(1);
  const [workingCode, setWorkingCode] = useState('');
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'error'>('saved');

  useEffect(() => {
    // Ensure the user is a student
    if (role !== 'student') {
      navigate('/login', { replace: true });
      return;
    }

    let active = true;

    const fetchTask = async (initial = false) => {
      try {
        if (initial) {
          setLoading(true);
          setError(null);
        }
        const data = await apiFetch(`/tasks/${id}`);
        if (!active) return;
        setTask(data);
        setWorkingCode(data.code_review_task?.source_code || '');
      } catch (err: any) {
        if (initial && active) setError(err.message || 'Failed to load task');
      } finally {
        if (initial && active) setLoading(false);
      }
    };

    fetchTask(true);
    const syncTimer = window.setInterval(() => fetchTask(false), 2000);

    return () => {
      active = false;
      window.clearInterval(syncTimer);
    };
  }, [navigate, role, id]);

  const handleSubmit = async () => {
    if (!task || task.type !== 'auto_check') return;

    setSubmissionResult(null);
    try {
      const response = await apiFetch(`/tasks/${id}/submit`, {
        method: 'POST',
        body: JSON.stringify({ answer_text: answer })
      });
      setSubmissionResult({ correct: response.is_correct, message: response.is_correct ? 'Correct!' : 'Incorrect. Try again.' });
      // Refresh task to update submission status
      const updatedTask = await apiFetch(`/tasks/${id}`);
      setTask(updatedTask);
    } catch (err: any) {
      setSubmissionResult({ correct: false, message: err.message || 'Submission failed' });
    }
  };

  const handleAddComment = async (lineNumber = newCommentLine, commentText = newComment) => {
    if (!task || task.type !== 'code_review' || !commentText.trim()) return;
    try {
      // For students, we don't need to specify student_id as it's taken from JWT
      await apiFetch(`/tasks/${id}/comments`, {
        method: 'POST',
        body: JSON.stringify({
          line_number: lineNumber,
          text: commentText
        })
      });
      // Clear the form
      setNewComment('');
      setNewCommentLine(1);
      // Refresh task to update comments
      const updatedTask = await apiFetch(`/tasks/${id}`);
      setTask(updatedTask);
    } catch (err: any) {
      alert('Failed to add comment: ' + (err.message || 'Unknown error'));
    }
  };

  if (loading) return <div className="loading-state">Loading task…</div>;
  if (error) return <div className="error">{error}</div>;
  if (!task) return <div>Task not found</div>;

  return (
    <div className="task-page">
      <div className="page-heading"><div className="page-heading__copy"><span className="eyebrow">Assignment</span><h2>{task.title}</h2><p className="page-subtitle">{task.description}</p></div><div className="task-meta"><span className="meta-chip">{task.type === 'code_review' ? 'Code review' : 'Auto-check'}</span><button className="button-ghost" onClick={() => navigate('/test')}>← All tasks</button></div></div>

      {task.type === 'auto_check' && (
        <div className="auto-check-task panel">
          <h3>Your Answer</h3>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={4}
            placeholder="Enter your answer here..."
          />
          <button
            className="button"
            onClick={handleSubmit}
            disabled={!answer.trim()}
          >
            Submit Answer
          </button>
          {submissionResult && (
            <div className={`submission-result submission-result--${submissionResult.correct ? 'success' : 'error'}`}>
              <strong>{submissionResult.message}</strong>
            </div>
          )}
        </div>
      )}

      {task.type === 'code_review' && (
        <div className="code-review-task">
          <div className="code-review-heading"><h3>{task.code_review_task?.student_mode === 'live' ? 'Live coding workspace' : 'Code to review'}</h3>{task.code_review_task?.student_mode === 'live' && <span className={`save-indicator save-indicator--${saveStatus}`}>{saveStatus === 'saving' ? 'Saving…' : saveStatus === 'error' ? 'Save failed' : 'All changes saved'}</span>}</div>
          <CodeReviewViewer
            key={`task-${id}`}
            code={workingCode}
            language={task.code_review_task?.language || null}
            comments={task.code_comments?.map((comment: any) => ({
              line_number: comment.line_number,
              text: comment.text,
              author_type: comment.author_type
            })) || []}
            enableCommenting={true}
            onCommentLineChange={setNewCommentLine}
            onAddComment={handleAddComment}
            readOnly={task.code_review_task?.student_mode !== 'live'}
            collaboration={{
              room: `task-${id}-student-${task.student_id}`,
              user: { name: 'Student', color: '#22d3ee', colorLight: '#22d3ee33' },
              onStatus: (status) => setSaveStatus(status === 'connected' ? 'saved' : status === 'connecting' ? 'saving' : 'error')
            }}
          />

        </div>
      )}
    </div>
  );
};

export default Task;
