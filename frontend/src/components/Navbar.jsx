import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.jsx'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path) => location.pathname === path ? 'text-blue-600 font-semibold' : 'text-gray-600 hover:text-blue-600'

  return (
    <nav className="bg-white border-b shadow-sm sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-xl font-bold text-blue-600">🚗 SDS</Link>
          <div className="flex items-center gap-4 text-sm">
            {user?.role === 'learner' && (
              <>
                <Link to="/" className={isActive('/')}>Dashboard</Link>
                <Link to="/book" className={isActive('/book')}>Đặt lịch</Link>
                <Link to="/my-bookings" className={isActive('/my-bookings')}>Lịch của tôi</Link>
              </>
            )}
            {user?.role === 'instructor' && (
              <Link to="/instructor" className={isActive('/instructor')}>Lịch dạy</Link>
            )}
            {user?.role === 'admin' && (
              <>
                <Link to="/admin" className={isActive('/admin')}>Dashboard</Link>
                <Link to="/instructor" className={isActive('/instructor')}>Ca học</Link>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-gray-500">{user?.name}</span>
          <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">{user?.role}</span>
          <button onClick={handleLogout} className="text-gray-500 hover:text-red-500 transition-colors">Đăng xuất</button>
        </div>
      </div>
    </nav>
  )
}
