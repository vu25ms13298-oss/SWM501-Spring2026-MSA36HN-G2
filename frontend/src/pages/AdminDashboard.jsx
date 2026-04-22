import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import client from '../api/client'

export default function AdminDashboard() {
  const [forecast, setForecast] = useState([])
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [overrideModal, setOverrideModal] = useState(null)
  const [overrideForm, setOverrideForm] = useState({ instructor_id: '', status: '' })
  const [msg, setMsg] = useState('')

  useEffect(() => {
    Promise.all([
      client.get('/admin/forecast?weeks=4'),
      client.get('/admin/sessions'),
    ]).then(([f, s]) => {
      setForecast(f.data)
      setSessions(s.data.slice(0, 20))
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  const handleOverride = async () => {
    try {
      const body = {}
      if (overrideForm.instructor_id) body.instructor_id = overrideForm.instructor_id
      if (overrideForm.status) body.status = overrideForm.status
      await client.put(`/admin/sessions/${overrideModal.id}`, body)
      setMsg('Cập nhật thành công!')
      setOverrideModal(null)
      const { data } = await client.get('/admin/sessions')
      setSessions(data.slice(0, 20))
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Cập nhật thất bại')
    }
  }

  if (loading) return <div className="text-center py-16 text-gray-400">Đang tải...</div>

  const hasAlert = forecast.some(f => f.alert)
  const chartData = forecast.map(f => ({
    name: f.week,
    'Dự báo đặt lịch': f.predicted_bookings,
    'Năng lực GV': f.instructor_capacity,
  }))

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        {hasAlert && (
          <span className="bg-red-100 text-red-700 px-3 py-1.5 rounded-full text-sm font-medium animate-pulse">
            ⚠️ Cảnh báo thiếu năng lực giảng dạy
          </span>
        )}
      </div>

      {msg && <div className="bg-green-50 text-green-700 rounded-lg p-3 mb-4">{msg}</div>}

      {/* Forecast Chart */}
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Dự báo nhu cầu đặt lịch</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="Dự báo đặt lịch" fill="#3b82f6" />
            <Bar dataKey="Năng lực GV" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-3 space-y-1">
          {forecast.map(f => (
            <div key={f.week} className={`flex justify-between text-sm px-2 py-1 rounded ${f.alert ? 'bg-red-50 text-red-700' : 'text-gray-600'}`}>
              <span>Tuần {f.week}</span>
              <span>Dự báo: {f.predicted_bookings} | Năng lực: {f.instructor_capacity} {f.alert ? '⚠️' : '✅'}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sessions List */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4">Quản lý ca học gần đây</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 border-b">
                <th className="text-left pb-3 pr-4">Thời gian</th>
                <th className="text-left pb-3 pr-4">Giáo viên</th>
                <th className="text-left pb-3 pr-4">Xe</th>
                <th className="text-left pb-3 pr-4">HV</th>
                <th className="text-left pb-3 pr-4">Trạng thái</th>
                <th className="text-left pb-3">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => (
                <tr key={s.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="py-3 pr-4">{format(new Date(s.slot_start), 'dd/MM HH:mm')}</td>
                  <td className="py-3 pr-4">{s.instructor_name}</td>
                  <td className="py-3 pr-4">{s.vehicle_plate}</td>
                  <td className="py-3 pr-4">{s.booking_count}/3</td>
                  <td className="py-3 pr-4">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                      s.status === 'confirmed' ? 'bg-green-100 text-green-700' :
                      s.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>{s.status}</span>
                  </td>
                  <td className="py-3">
                    <button
                      onClick={() => { setOverrideModal(s); setOverrideForm({ instructor_id: '', status: '' }) }}
                      className="text-blue-600 hover:underline text-xs"
                    >Override</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Override Modal */}
      {overrideModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm mx-4">
            <h2 className="text-lg font-bold mb-4">Override Ca học</h2>
            <p className="text-sm text-gray-500 mb-4">{format(new Date(overrideModal.slot_start), 'dd/MM/yyyy HH:mm')} — {overrideModal.instructor_name}</p>
            <div className="space-y-3 mb-4">
              <div>
                <label className="text-sm font-medium text-gray-700">ID Giáo viên mới (tuỳ chọn)</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1 text-sm"
                  placeholder="UUID giáo viên"
                  value={overrideForm.instructor_id}
                  onChange={e => setOverrideForm({ ...overrideForm, instructor_id: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Trạng thái</label>
                <select
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 mt-1 text-sm"
                  value={overrideForm.status}
                  onChange={e => setOverrideForm({ ...overrideForm, status: e.target.value })}
                >
                  <option value="">-- Không thay đổi --</option>
                  <option value="confirmed">confirmed</option>
                  <option value="pending_reassignment">pending_reassignment</option>
                  <option value="cancelled">cancelled</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setOverrideModal(null)} className="flex-1 border border-gray-300 py-2 rounded-lg text-sm">Hủy</button>
              <button onClick={handleOverride} className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm hover:bg-blue-700">Lưu</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
