import { useState, useEffect, useRef } from 'react'
import { format } from 'date-fns'
import client from '../api/client'

const CONV_ID_KEY = 'sds_conversation_id'

function getOrCreateConvId() {
  let id = sessionStorage.getItem(CONV_ID_KEY)
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem(CONV_ID_KEY, id)
  }
  return id
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [convId] = useState(getOrCreateConvId)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (open && messages.length === 0) {
      // Load history
      client.get(`/chat/history/${convId}`)
        .then(({ data }) => setMessages(data))
        .catch(() => {
          setMessages([{
            id: 'welcome',
            role: 'assistant',
            content: 'Xin chào! Tôi là trợ lý AI của SDS. Tôi có thể giúp gì cho bạn?',
            created_at: new Date().toISOString(),
          }])
        })
    }
  }, [open])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const text = input.trim()
    setInput('')
    const userMsg = { id: Date.now() + '-u', role: 'user', content: text, created_at: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    try {
      const { data } = await client.post('/chat/message', {
        conversation_id: convId,
        message: text,
      })
      const assistantMsg = {
        id: Date.now() + '-a',
        role: 'assistant',
        content: data.response,
        created_at: new Date().toISOString(),
        escalated: data.escalated,
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + '-e',
        role: 'assistant',
        content: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.',
        created_at: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  const escalate = async () => {
    try {
      await client.post('/chat/escalate', { conversation_id: convId })
      setMessages(prev => [...prev, {
        id: Date.now() + '-esc',
        role: 'staff',
        content: '✅ Cuộc hội thoại đã được chuyển cho nhân viên hỗ trợ. Chúng tôi sẽ liên hệ với bạn sớm.',
        created_at: new Date().toISOString(),
      }])
    } catch {
      alert('Không thể kết nối nhân viên hỗ trợ lúc này.')
    }
  }

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all flex items-center justify-center text-2xl z-50"
      >
        {open ? '✕' : '💬'}
      </button>

      {/* Chat window */}
      {open && (
        <div className="fixed bottom-24 right-6 w-80 h-[480px] bg-white rounded-2xl shadow-2xl border flex flex-col z-50">
          {/* Header */}
          <div className="bg-blue-600 text-white px-4 py-3 rounded-t-2xl flex items-center justify-between">
            <div>
              <p className="font-semibold text-sm">Trợ lý SDS</p>
              <p className="text-xs opacity-80">Hỗ trợ 24/7</p>
            </div>
            <button onClick={escalate} className="text-xs bg-white/20 px-2 py-1 rounded-lg hover:bg-white/30">
              👤 Nhân viên
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : msg.role === 'staff'
                    ? 'bg-orange-50 text-orange-800 border border-orange-200 rounded-bl-sm'
                    : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-2 text-sm text-gray-500">
                  <span className="animate-pulse">●●●</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t flex gap-2">
            <input
              type="text"
              placeholder="Nhập tin nhắn..."
              className="flex-1 border border-gray-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="bg-blue-600 text-white px-3 py-2 rounded-xl hover:bg-blue-700 disabled:opacity-50 text-sm"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  )
}
