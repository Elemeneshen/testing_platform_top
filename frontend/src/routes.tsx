import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import TeacherLogin from './pages/TeacherLogin';
import Test from './pages/Test';
import Task from './pages/Task';
import TeacherDashboard from './pages/TeacherDashboard';
import TeacherTaskReview from './pages/TeacherTaskReview';
import TeacherTestCreate from './pages/TeacherTestCreate';
import TeacherTaskProgress from './pages/TeacherTaskProgress';
import StudentRegister from './pages/StudentRegister';
import StudentGroupSelect from './pages/StudentGroupSelect';
import { useAuthStore } from './store/authStore';

const ProtectedRoute = ({ children, expectedRole }: { children: React.ReactNode; expectedRole: 'student' | 'teacher' }) => {
  const { role, isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to={expectedRole === 'student' ? '/login' : '/teacher/login'} replace />;
  if (role !== expectedRole) return <Navigate to={role === 'student' ? '/login' : '/teacher/login'} replace />;
  return children;
};

const AppRoutes: React.FC = () => {
  return (
      <Layout>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<StudentRegister />} />
          <Route path="/teacher/login" element={<TeacherLogin />} />

          {/* Protected student routes */}
          <Route
            path="/student/group"
            element={
              <ProtectedRoute expectedRole="student">
                <StudentGroupSelect />
              </ProtectedRoute>
            }
          />
          <Route
            path="/test"
            element={
              <ProtectedRoute expectedRole="student">
                <Test />
              </ProtectedRoute>
            }
          />
          <Route
            path="/task/:id"
            element={
              <ProtectedRoute expectedRole="student">
                <Task />
              </ProtectedRoute>
            }
          />

          {/* Protected teacher routes */}
          <Route
            path="/teacher/dashboard"
            element={
              <ProtectedRoute expectedRole="teacher">
                <TeacherDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/task/:id"
            element={
              <ProtectedRoute expectedRole="teacher">
                <TeacherTaskProgress />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/task/:id/review/:studentId"
            element={
              <ProtectedRoute expectedRole="teacher">
                <TeacherTaskReview />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher/tests/create"
            element={
              <ProtectedRoute expectedRole="teacher">
                <TeacherTestCreate />
              </ProtectedRoute>
            }
          />

          {/* Redirect root to login */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          {/* Catch-all for 404 */}
          <Route path="*" element={<h1>404 - Not Found</h1>} />
        </Routes>
      </Layout>
  );
};

export default AppRoutes;
