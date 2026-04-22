import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import client from '../api/client'

export default function MyBookingsPage() {
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cancelling, setCancelling] = useState(null)

  const fetchBookings = async () => {
    setLoading(true)
    try {
      const { data } = await client.get('/bookings/me')
      setBookings(data)
    } catch (err) {
      setError('Không thể tải lịch học')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchBookings() }, [])

  const cancelBooking = async (id) => {
    try {
      const { data } = await client.delete(`/bookings/${id}`)
      const adj = data.credit_adjustment
      const msg = adj > 0 ? `Hủy thành công, hoàn ${adj} tín chỉ.` :
                  adj === 0 ? 'Hủy thành công, không hoàn tín chỉ.' :
                  `Hủy thành công, bị trừ thêm ${Math.abs(adj)} tín chỉ do hủy muộn.`
      alert(msg)
      fetchBookings()
    } catch (err) {
      alert(err.response?.data?.detail || 'Hủy lịch thất bại')
    } finally {
      setCancelling(null)
    }
  }

  const statusBadge = (status) => {
    if (status === 'confirmed') return <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Đã xác nhận</span>
    return <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Đã hủy</span>
  }

  if (loading) return <div className="text-center py-16 text-gray-400">Đang tải...</div>

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Lịch học của tôi</h1>

      {error && <div className="bg-red-50 text-red-600 rounded-lg p-3 mb-4">{error}</div>}

      {bookings.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-2">📚</p>
          <p>Bạn chưa có lịch học nào</p>
        </div>
      ) : (
        <div className="space-y-3">
          {bookings.map((b) => (
            <div key={b.id} className="bg-white rounded-xl shadow-sm border p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    {b.session_start && (
                      <span className="font-semibold">
                        {format(new Date(b.session_start), 'HH:mm – dd/MM/yyyy')}
                      </span>
                    )}
                    {statusBadge(b.status)}
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    {b.instructor_name && <p>👨‍🏫 Giáo viên: {b.instructor_name}</p>}
                    {b.vehicle_plate && <p>🚗 Xe: {b.vehicle_plate}</p>}
                    <p>📅 Đặt lúc: {format(new Date(b.booked_at), 'dd/MM/yyyy HH:mm')}</p>
                    {b.cancelled_at && <p>❌ Hủy lúc: {format(new Date(b.cancelled_at), 'dd/MM/yyyy HH:mm')}</p>}
                  </div>
                </div>
                {b.status === 'confirmed' && (
                  <button
                    onClick={() => setCancelling(b)}
                    className="text-red-500 border border-red-300 px-3 py-1.5 rounded-lg text-sm hover:bg-red-50 transition-colors"
                  >
                    Hủy lịch
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cancel confirm modal */}
      {cancelling && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm mx-4">
            <h2 className="text-lg font-bold mb-3">Xác nhận hủy lịch</h2>
            <p className="text-sm text-gray-600 mb-2">
              Buổi học: {cancelling.session_start && format(new Date(cancelling.session_start), 'HH:mm dd/MM/yyyy')}
            </p>
            <p className="text-sm text-orange-600 bg-orange-50 rounded-lg p-3 mb-4">
              ⚠️ Hủy trong vòng 2h: mất thêm 1 tín chỉ. Hủy trước 12h: hoàn đủ 1 tín chỉ.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setCancelling(null)} className="flex-1 border border-gray-300 py-2 rounded-lg">Không</button>
              <button onClick={() => cancelBooking(cancelling.id)} className="flex-1 bg-red-500 text-white py-2 rounded-lg hover:bg-red-600">Xác nhận hủy</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
