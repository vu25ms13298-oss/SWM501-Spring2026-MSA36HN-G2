import { format, addDays, startOfWeek } from 'date-fns'
import { vi } from 'date-fns/locale'

export default function SlotCalendar({ slots, onSelectSlot }) {
  if (!slots || slots.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <p>Không có ca học nào</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {slots.map((slot) => (
        <div
          key={slot.session_id}
          className="flex items-center justify-between border rounded-xl p-3 hover:bg-blue-50 cursor-pointer transition-colors"
          onClick={() => onSelectSlot && onSelectSlot(slot)}
        >
          <div>
            <span className="font-medium">
              {format(new Date(slot.slot_start), 'HH:mm')} – {format(new Date(slot.slot_end), 'HH:mm')}
            </span>
            <span className="text-sm text-gray-500 ml-3">{slot.instructor_name}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">{slot.available_spots} chỗ trống</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              slot.best_match_score >= 0.5 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
            }`}>
              {Math.round(slot.best_match_score * 100)}% match
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
