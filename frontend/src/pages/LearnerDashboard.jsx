import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import client from '../api/client'
import { useAuth } from '../hooks/useAuth.jsx'

export default function LearnerDashboard() {
  const { user } = useAuth()
  const [bookings, setBookings] = useState([])
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      client.get('/bookings/me'),
      client.get('/auth/me'),
    ]).then(([b, p]) => {
      setBookings(b.data)
      setProfile(p.data)
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-center py-16 text-gray-400">Đang tải...</div>

  const upcoming = bookings.filter(b => b.status === 'confirmed' && b.session_start && new Date(b.session_start) > new Date())
  const completed = bookings.filter(b => b.status === 'confirmed' && b.session_start && new Date(b.session_start) <= new Date())
  const nextLesson = upcoming.sort((a, b) => new Date(a.session_start) - new Date(b.session_start))[0]

  const skillLabel = { beginner: 'Sơ cấp', intermediate: 'Trung cấp', advanced: 'Nâng cao' }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Chào, {user?.name} 👋</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
          <p className="text-3xl font-bold text-blue-600">{profile?.lesson_credits ?? '—'}</p>
          <p className="text-sm text-gray-500 mt-1">Tín chỉ còn lại</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
          <p className="text-3xl font-bold text-green-600">{upcoming.length}</p>
          <p className="text-sm text-gray-500 mt-1">Lịch sắp tới</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
          <p className="text-3xl font-bold text-purple-600">{completed.length}</p>
          <p className="text-sm text-gray-500 mt-1">Buổi đã học</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
          <p className="text-3xl font-bold text-orange-500">{skillLabel[profile?.skill_level] || '—'}</p>
          <p className="text-sm text-gray-500 mt-1">Trình độ</p>
        </div>
      </div>

      {/* Next lesson */}
      {nextLesson && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
          <h2 className="font-semibold text-blue-800 mb-2">📅 Buổi học tiếp theo</h2>
          <p className="text-blue-700">
            {format(new Date(nextLesson.session_start), 'HH:mm — EEEE, dd/MM/yyyy')}
          </p>
          {nextLesson.instructor_name && <p className="text-blue-600 text-sm">Giáo viên: {nextLesson.instructor_name}</p>}
          {nextLesson.vehicle_plate && <p className="text-blue-600 text-sm">Xe: {nextLesson.vehicle_plate}</p>}
        </div>
      )}

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <Link to="/book" className="bg-blue-600 text-white rounded-xl p-4 flex items-center gap-3 hover:bg-blue-700 transition-colors">
          <span className="text-2xl">📅</span>
          <div>
            <p className="font-semibold">Đặt lịch học</p>
            <p className="text-sm opacity-80">Chọn ca học phù hợp</p>
          </div>
        </Link>
        <Link to="/my-bookings" className="bg-white border rounded-xl p-4 flex items-center gap-3 hover:bg-gray-50 transition-colors">
          <span className="text-2xl">📋</span>
          <div>
            <p className="font-semibold">Lịch học của tôi</p>
            <p className="text-sm text-gray-500">Xem và quản lý lịch</p>
          </div>
        </Link>
      </div>

      {/* Recent bookings */}
      {bookings.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <h2 className="font-semibold mb-3">Lịch học gần đây</h2>
          <div className="space-y-2">
            {bookings.slice(0, 5).map(b => (
              <div key={b.id} className="flex justify-between items-center text-sm border-b last:border-0 pb-2 last:pb-0">
                <div>
                  {b.session_start && <span>{format(new Date(b.session_start), 'dd/MM/yyyy HH:mm')}</span>}
                  {b.instructor_name && <span className="text-gray-500 ml-2">— {b.instructor_name}</span>}
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs ${b.status === 'confirmed' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {b.status === 'confirmed' ? 'Đã đặt' : 'Đã hủy'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
