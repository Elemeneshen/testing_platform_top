import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiFetch } from '../utils/api';
import { useForm } from 'react-hook-form';
import type { FieldErrors } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import CodeReviewViewer from '../components/CodeReviewViewer';

// Discriminated union schema — используется только для валидации и финального payload
const autoCheckSchema = z.object({
  type: z.literal('auto_check'),
  checker_type: z.enum(['exact', 'regex', 'tokenized']),
  expected_value: z.string().nonempty('Expected value is required'),
});

const codeReviewSchema = z.object({
  type: z.literal('code_review'),
  language: z.enum(['java', 'python', 'javascript', 'html', 'css']),
  source_code: z.string().nonempty('Source code is required'),
  student_mode: z.enum(['review', 'live']),
});

const baseTaskSchema = z.object({
  title: z.string().nonempty('Title is required'),
  description: z.string().nonempty('Description is required'),
});

const taskSchema = baseTaskSchema.and(
  z.discriminatedUnion('type', [autoCheckSchema, codeReviewSchema])
);

const formSchema = taskSchema.and(z.object({ group_ids: z.array(z.number()), student_ids: z.array(z.number()), is_visible: z.boolean() })).refine((data) => data.group_ids.length > 0 || data.student_ids.length > 0, { message: 'Select at least one group or student', path: ['group_ids'] });

// Плоский тип для useForm — все условные поля опциональны
type FormShape = {
  title: string;
  description: string;
  type: 'auto_check' | 'code_review';
  checker_type?: 'exact' | 'regex' | 'tokenized';
  expected_value?: string;
  language?: 'java' | 'python' | 'javascript' | 'html' | 'css';
  source_code?: string;
  student_mode?: 'review' | 'live';
  group_ids: number[];
  student_ids: number[];
  is_visible: boolean;
};

const TeacherTaskCreate: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuthStore();
  const [submitLoading, setSubmitLoading] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [assignmentGroups, setAssignmentGroups] = useState<Array<{ id: number; name: string; students: Array<{ id: number; full_name: string; username: string }> }>>([]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    watch,
    setValue,
  } = useForm<FormShape>({
    resolver: zodResolver(formSchema) as any, // схема union, форма — плоский тип, приводим намеренно
    defaultValues: {
      title: '',
      description: '',
      type: 'auto_check',
      checker_type: 'exact',
      expected_value: '',
      language: 'java',
      source_code: '',
      student_mode: 'review',
      group_ids: [],
      student_ids: [],
      is_visible: false,
    },
  });

  const typedErrors = errors as FieldErrors<FormShape>;

  const type = watch('type');
  const selectedGroups = watch('group_ids');
  const selectedStudents = watch('student_ids');

  useEffect(() => { apiFetch('/admin/assignment-options').then((data) => setAssignmentGroups(data.groups)).catch((err) => setSubmitError(err.message)); }, []);

  useEffect(() => {
    if (type === 'auto_check') {
      setValue('language', undefined);
      setValue('source_code', '');
      setValue('student_mode', undefined);
    } else if (type === 'code_review') {
      setValue('checker_type', undefined);
      setValue('expected_value', '');
      setValue('student_mode', 'review');
    }
  }, [type, setValue]);

  const onSubmit = async (data: FormShape) => {
    setSubmitLoading(true);
    setSubmitError(null);
    setSubmitSuccess(null);

    try {
      const task: any = {
        title: data.title.trim(),
        description: data.description.trim(),
        type: data.type,
      };
      if (data.type === 'auto_check') {
        task.checker_type = data.checker_type;
        task.expected_value = data.expected_value;
      } else if (data.type === 'code_review') {
        task.language = data.language;
        task.source_code = data.source_code;
        task.student_mode = data.student_mode;
      }

      const result = await apiFetch('/admin/tasks', {
        method: 'POST',
        body: JSON.stringify({ ...task, group_ids: data.group_ids, student_ids: data.student_ids, is_visible: data.is_visible }),
      });

      setSubmitSuccess('Task created successfully.');
      reset();
      navigate(`/teacher/task/${result.id}`);
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to create task');
    } finally {
      setSubmitLoading(false);
    }
  };

  if (role !== 'teacher') {
    navigate('/teacher/login', { replace: true });
    return null;
  }

  return (
    <div className="teacher-task-create">
      <div className="page-heading"><div className="page-heading__copy"><span className="eyebrow">Task builder</span><h2>Create a new task</h2><p className="page-subtitle">Prepare an assignment, choose its recipients and publish when ready.</p></div><button type="button" onClick={() => navigate('/teacher/dashboard')} className="button-ghost">← Dashboard</button></div>
      {submitSuccess && <div className="success">{submitSuccess}</div>}
      {submitError && <div className="error">{submitError}</div>}
      <form onSubmit={handleSubmit(onSubmit)} className="task-form" style={{ width: '100%', maxWidth: '980px' }}>
        <div className="form-group">
          <label htmlFor="title">Task title:</label>
          <input
            type="text"
            id="title"
            {...register('title')}
            className={`input ${typedErrors.title ? 'error' : ''}`}
          />
          {typedErrors.title && (
            <span className="error-message" style={{ color: 'red', fontSize: '0.875rem' }}>
              {typedErrors.title.message}
            </span>
          )}
        </div>

        <h3>Assign to</h3>
        <div className="assignment-picker">
          <div><span className="assignment-picker__label">Groups</span>{assignmentGroups.map((group) => <label className="assignment-option" key={group.id}><input type="checkbox" checked={selectedGroups.includes(group.id)} onChange={(event) => setValue('group_ids', event.target.checked ? [...selectedGroups, group.id] : selectedGroups.filter((id) => id !== group.id), { shouldValidate: true })} /><span><b>{group.name}</b><small>{group.students.length} students</small></span></label>)}</div>
          <div><span className="assignment-picker__label">Individual students</span>{assignmentGroups.flatMap((group) => group.students.map((student) => <label className="assignment-option" key={student.id}><input type="checkbox" checked={selectedStudents.includes(student.id)} onChange={(event) => setValue('student_ids', event.target.checked ? [...selectedStudents, student.id] : selectedStudents.filter((id) => id !== student.id), { shouldValidate: true })} /><span><b>{student.full_name}</b><small>@{student.username} · {group.name}</small></span></label>))}</div>
        </div>
        {(typedErrors as any).group_ids && <span className="error-message">{(typedErrors as any).group_ids.message}</span>}

        <label className="publish-toggle"><input type="checkbox" {...register('is_visible')} /><span><b>Publish immediately</b><small>Students will see this task in their workspace. Turn it off to keep the task hidden.</small></span></label>

        <div className="form-group">
          <label htmlFor="description">Description:</label>
          <textarea
            id="description"
            {...register('description')}
            className={`input ${typedErrors.description ? 'error' : ''}`}
            rows={4}
          />
          {typedErrors.description && (
            <span className="error-message" style={{ color: 'red', fontSize: '0.875rem' }}>
              {typedErrors.description.message}
            </span>
          )}
        </div>

        <div className="form-group">
          <fieldset>
            <legend>Type:</legend>
            <div className="type-radio-group">
              <label>
                <input
                  type="radio"
                  value="auto_check"
                  checked={type === 'auto_check'}
                  onChange={() => setValue('type', 'auto_check', { shouldValidate: true })}
                />
                Auto-check
              </label>
              <label style={{ marginLeft: '1rem' }}>
                <input
                  type="radio"
                  value="code_review"
                  checked={type === 'code_review'}
                  onChange={() => setValue('type', 'code_review', { shouldValidate: true })}
                />
                Code review
              </label>
            </div>
          </fieldset>
        </div>

        {type === 'auto_check' && (
          <>
            <div className="form-group">
              <label htmlFor="checkerType">Checker Type:</label>
              <select
                id="checkerType"
                {...register('checker_type')}
                className={`select ${typedErrors.checker_type ? 'error' : ''}`}
              >
                <option value="exact">Exact match</option>
                <option value="regex">Regular expression</option>
                <option value="tokenized">Tokenized comparison</option>
              </select>
              {typedErrors.checker_type && (
                <span className="error-message" style={{ color: 'red', fontSize: '0.875rem' }}>
                  {typedErrors.checker_type.message}
                </span>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="expectedValue">Expected Value:</label>
              <input
                type="text"
                id="expectedValue"
                {...register('expected_value')}
                className={`input ${typedErrors.expected_value ? 'error' : ''}`}
                placeholder={watch('checker_type') === 'regex' ? 'e.g., git commit -m ".*"' : ''}
              />
              {typedErrors.expected_value && (
                <span className="error-message" style={{ color: 'red', fontSize: '0.875rem' }}>
                  {typedErrors.expected_value.message}
                </span>
              )}
            </div>
          </>
        )}

        {type === 'code_review' && (
          <>
            <div className="form-group">
              <label htmlFor="languageSelect">Language:</label>
              <select
                id="languageSelect"
                {...register('language')}
                className={`select ${typedErrors.language ? 'error' : ''}`}
              >
                <option value="java">Java</option>
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="html">HTML</option>
                <option value="css">CSS</option>
              </select>
              {typedErrors.language && (
                <span className="error-message" style={{ color: 'red', fontSize: '0.875rem' }}>
                  {typedErrors.language.message}
                </span>
              )}
            </div>
            <div className="form-group">
              <label>Student editor mode:</label>
              <div className="mode-picker">
                <label className={watch('student_mode') === 'review' ? 'mode-picker__option mode-picker__option--active' : 'mode-picker__option'}>
                  <input type="radio" value="review" checked={watch('student_mode') === 'review'} onChange={() => setValue('student_mode', 'review', { shouldValidate: true })} />
                  <span><b>Review only</b><small>Students can read the code and leave comments.</small></span>
                </label>
                <label className={watch('student_mode') === 'live' ? 'mode-picker__option mode-picker__option--active' : 'mode-picker__option'}>
                  <input type="radio" value="live" checked={watch('student_mode') === 'live'} onChange={() => setValue('student_mode', 'live', { shouldValidate: true })} />
                  <span><b>Live coding</b><small>Each student edits an autosaved private copy.</small></span>
                </label>
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="sourceCode">Source Code:</label>
              <div>
                <CodeReviewViewer
                  code={watch('source_code') ?? ''}
                  language={watch('language') ?? null}
                  comments={[]}
                  enableCommenting={false}
                  onCommentLineChange={() => {}}
                  onAddComment={() => {}}
                  readOnly={false}
                  onCodeChange={(code) => setValue('source_code', code, { shouldValidate: true })}
                  style={{ height: '520px', width: '100%' }}
                />
              </div>
              {typedErrors.source_code && (
                <span className="error-message" style={{ color: 'red', fontSize: '0.875rem' }}>
                  {typedErrors.source_code.message}
                </span>
              )}
            </div>
          </>
        )}

        <div className="form-actions">
          <button type="submit" disabled={submitLoading || isSubmitting} className="button">
            {submitLoading ? 'Creating...' : 'Create Task'}
          </button>
          <button type="button" onClick={() => navigate('/teacher/dashboard')} className="button-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default TeacherTaskCreate;
