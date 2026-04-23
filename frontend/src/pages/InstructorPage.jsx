import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { vi } from 'date-fns/locale'
import client from '../api/client'

function getISOWeek(date) {
  const d = new Date(date)
  const year = d.getFullYear()
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7))
  const week1 = new Date(d.getFullYear(), 0, 4)
  const week = 1 + Math.round(((d - week1) / 86400000 - 3 + ((week1.getDay() + 6) % 7)) / 7)
  return `${year}-${String(week).padStart(2, '0')}`
}

export default function InstructorPage() {
  const [week, setWeek] = useState(getISOWeek(new Date()))
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchSchedule = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await client.get(`/instructor/schedule?week=${week}`)
      setSessions(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể tải lịch dạy')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchSchedule() }, [week])

  const skillLabel = { beginner: 'Sơ cấp', intermediate: 'Trung cấp', advanced: 'Nâng cao' }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Lịch dạy</h1>

      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4 mb-6">
        <p className="text-sm text-green-900">
          <span className="font-semibold">Smart Grouping:</span> Hệ thống tự động ghép học viên cùng trình độ vào lớp của bạn.
          Mỗi ca tối đa 3 học viên, ưu tiên nhóm có cùng level để tăng hiệu quả học tập.
        </p>
      </div>

      <div className="flex gap-4 mb-6 items-center">
        <div>
          <label className="text-sm font-medium text-gray-700 mr-2">Tuần:</label>
          <input
            type="week"
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={week.replace(/^(\d{4})-(\d{2})$/, '$1-W$2')}
            onChange={e => {
            const val = e.target.value
            if (val) {
              const formatted = val.replace('-W', '-')
              setWeek(formatted)
            }
          }}
          />
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-600 rounded-lg p-3 mb-4">{error}</div>}
      {loading && <div className="text-center py-8 text-gray-400">Đang tải...</div>}

      {!loading && sessions.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-2">📋</p>
          <p>Không có ca dạy trong tuần này</p>
        </div>
      )}

      <div className="space-y-3">
        {sessions.map((s) => (
          <div key={s.session_id} className="bg-white rounded-xl shadow-sm border p-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-semibold text-lg">
                    {format(new Date(s.slot_start), 'HH:mm')} – {format(new Date(s.slot_end), 'HH:mm')}
                  </span>
                  <span className="text-sm text-gray-500">
                    {format(new Date(s.slot_start), 'EEEE, dd/MM', { locale: vi })}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    s.status === 'confirmed' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}>{s.status === 'confirmed' ? 'Xác nhận' : s.status}</span>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>🚗 Xe: {s.vehicle_plate} ({s.vehicle_type === 'manual' ? 'Số sàn' : 'Số tự động'})</p>
                  <p>👥 Học viên: <span className="font-medium">{s.learner_count}/3</span></p>
                  {s.skill_levels.length > 0 && (
                    <p>📊 Trình độ: {s.skill_levels.map(sk => skillLabel[sk] || sk).join(', ')}</p>
                  )}
                </div>
              </div>
              <div className="flex gap-1">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className={`w-4 h-4 rounded-full ${i < s.learner_count ? 'bg-blue-500' : 'bg-gray-200'}`} />
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
