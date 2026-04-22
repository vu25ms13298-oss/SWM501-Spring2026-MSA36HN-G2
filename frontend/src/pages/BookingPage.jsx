import { useState } from 'react'
import { format, addDays } from 'date-fns'
import { vi } from 'date-fns/locale'
import client from '../api/client'

export default function BookingPage() {
  const [date, setDate] = useState(format(addDays(new Date(), 2), 'yyyy-MM-dd'))
  const [slots, setSlots] = useState([])
  const [loading, setLoading] = useState(false)
  const [booking, setBooking] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const fetchSlots = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await client.get(`/slots?date=${date}`)
      setSlots(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể tải danh sách lịch')
    } finally {
      setLoading(false)
    }
  }

  const confirmBooking = async (sessionId) => {
    setError('')
    setSuccess('')
    try {
      await client.post('/bookings', { session_id: sessionId })
      setSuccess('Đặt lịch thành công! Tín chỉ đã được trừ.')
      setBooking(null)
      fetchSlots()
    } catch (err) {
      setError(err.response?.data?.detail || 'Đặt lịch thất bại')
    }
  }

  const skillBadge = (score) => {
    if (score >= 0.7) return <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Phù hợp cao</span>
    if (score >= 0.4) return <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">Phù hợp vừa</span>
    return <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">Phù hợp thấp</span>
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Đặt lịch học</h1>

      <div className="bg-white rounded-xl shadow-sm border p-4 mb-6 flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Chọn ngày</label>
          <input
            type="date"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={date}
            min={format(addDays(new Date(), 1), 'yyyy-MM-dd')}
            onChange={e => setDate(e.target.value)}
          />
        </div>
        <button
          onClick={fetchSlots}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60"
        >
          {loading ? 'Đang tải...' : 'Tìm lịch'}
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-600 rounded-lg p-3 mb-4">{error}</div>}
      {success && <div className="bg-green-50 border border-green-200 text-green-600 rounded-lg p-3 mb-4">{success}</div>}

      {slots.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-4xl mb-2">📅</p>
          <p>Chọn ngày và nhấn "Tìm lịch" để xem các ca học còn trống</p>
        </div>
      )}

      <div className="space-y-3">
        {slots.map((slot) => (
          <div key={slot.session_id} className="bg-white rounded-xl shadow-sm border p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-lg font-semibold">
                    {format(new Date(slot.slot_start), 'HH:mm')} – {format(new Date(slot.slot_end), 'HH:mm')}
                  </span>
                  {skillBadge(slot.best_match_score)}
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>👨‍🏫 Giáo viên: <span className="font-medium">{slot.instructor_name}</span></p>
                  <p>🚗 Xe: {slot.vehicle_plate} ({slot.vehicle_type === 'manual' ? 'Số sàn' : 'Số tự động'})</p>
                  <p>👥 Còn trống: <span className="font-medium text-green-600">{slot.available_spots}/{slot.total_capacity}</span> chỗ</p>
                </div>
              </div>
              <button
                onClick={() => setBooking(slot)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
              >
                Đặt lịch
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Confirm Modal */}
      {booking && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm mx-4">
            <h2 className="text-lg font-bold mb-4">Xác nhận đặt lịch</h2>
            <div className="space-y-2 text-sm text-gray-600 mb-6">
              <p>🕐 Thời gian: {format(new Date(booking.slot_start), 'HH:mm dd/MM/yyyy')}</p>
              <p>👨‍🏫 Giáo viên: {booking.instructor_name}</p>
              <p>🚗 Xe: {booking.vehicle_plate}</p>
              <p className="text-orange-600 font-medium">⚠️ Sẽ trừ 1 tín chỉ</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setBooking(null)}
                className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-50"
              >Hủy</button>
              <button
                onClick={() => confirmBooking(booking.session_id)}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
              >Xác nhận</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
