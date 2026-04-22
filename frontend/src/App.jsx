import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth.jsx'
import LoginPage from './pages/LoginPage'
import BookingPage from './pages/BookingPage'
import MyBookingsPage from './pages/MyBookingsPage'
import InstructorPage from './pages/InstructorPage'
import AdminDashboard from './pages/AdminDashboard'
import LearnerDashboard from './pages/LearnerDashboard'
import Navbar from './components/Navbar'
import ChatWidget from './components/ChatWidget'

function ProtectedRoute({ children, roles }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return children
}

function AppRoutes() {
  const { user } = useAuth()

  return (
    <>
      {user && <Navbar />}
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
        <Route path="/" element={
          <ProtectedRoute>
            {user?.role === 'learner' ? <LearnerDashboard /> :
             user?.role === 'instructor' ? <InstructorPage /> :
             user?.role === 'admin' ? <AdminDashboard /> :
             <LearnerDashboard />}
          </ProtectedRoute>
        } />
        <Route path="/book" element={<ProtectedRoute roles={['learner']}><BookingPage /></ProtectedRoute>} />
        <Route path="/my-bookings" element={<ProtectedRoute roles={['learner']}><MyBookingsPage /></ProtectedRoute>} />
        <Route path="/instructor" element={<ProtectedRoute roles={['instructor', 'admin']}><InstructorPage /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute roles={['admin']}><AdminDashboard /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {user && <ChatWidget />}
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
