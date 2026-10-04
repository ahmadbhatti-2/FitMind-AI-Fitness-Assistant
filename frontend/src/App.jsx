import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import AuthProvider from './auth/AuthContext';
import useAuth from './auth/useAuth';
import Layout from './components/Layout';
import AICoach from './pages/AICoach';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Nutrition from './pages/Nutrition';
import Profile from './pages/Profile';
import Progress from './pages/Progress';
import Workout from './pages/Workout';

function AuthenticatedApp() {
  const { user } = useAuth();
  if (!user) return <Login />;

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/coach" element={<AICoach />} />
        <Route path="/workouts" element={<Workout />} />
        <Route path="/nutrition" element={<Nutrition />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AuthenticatedApp />
      </AuthProvider>
    </BrowserRouter>
  );
}
