import { useState, useEffect, useRef } from 'react'
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
  const [suggestedQuestions, setSuggestedQuestions] = useState([])
  const bottomRef = useRef(null)
  const quickPrompts = [
    'Tên tôi là gì?',
    'Buổi học tiếp theo của tôi là khi nào?',
    'Làm sao để đặt lịch học?',
  ]

  const mockResponses = {
    'Lam sao de dat lich hoc?': 'Ban co the vao trang Dat lich hoc, chon ngay mong muon, xem cac ca hoc trong ngay, kiem tra diem phu hop va xac nhan. He thong se tu dong tru 1 tin chi cho moi buoi hoc.',
    'Toi con bao nhieu tin chi?': 'Ban co the xem so tin chi hien tai tren dashboard hoc vien. Moi tin chi tuong duong 1 buoi hoc 60 phut.',
    'Toi co the huy lich khong?': 'Ban co the huy lich tai trang Lich hoc cua toi. Huy truoc 12 gio se duoc hoan tin chi day du, huy qua sat gio hoc se khong duoc hoan hoac bi tru them tin chi theo quy dinh.',
  }

  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

  const waitForRealisticLatency = async (startTime) => {
    // Keep a realistic delay so assistant replies feel like a real retrieval + generation flow.
    const minLatency = 900
    const jitter = Math.floor(Math.random() * 700)
    const targetLatency = minLatency + jitter
    const elapsed = Date.now() - startTime
    const remaining = targetLatency - elapsed
    if (remaining > 0) {
      await wait(remaining)
    }
  }

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
    setSuggestedQuestions([])

    const userMsg = { id: Date.now() + '-u', role: 'user', content: text, created_at: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    const requestStartTime = Date.now()

    try {
      const { data } = await client.post('/chat/message', {
        conversation_id: convId,
        message: text,
      })

      await waitForRealisticLatency(requestStartTime)

      const assistantMsg = {
        id: Date.now() + '-a',
        role: 'assistant',
        content: data.response,
        created_at: new Date().toISOString(),
        escalated: data.escalated,
      }
      setMessages(prev => [...prev, assistantMsg])

      if (data.api_limited && data.suggested_questions?.length) {
        setSuggestedQuestions(data.suggested_questions)
      }
    } catch {
      await waitForRealisticLatency(requestStartTime)

      setMessages(prev => [...prev, {
        id: Date.now() + '-e',
        role: 'assistant',
        content: 'Xin loi, da co loi xay ra. Vui long thu lai.',
        created_at: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  const selectSuggestedQuestion = async (question) => {
    const userMsg = {
      id: Date.now() + '-u',
      role: 'user',
      content: question,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setSuggestedQuestions([])
    setLoading(true)

    await wait(1200)

    setMessages(prev => [...prev, {
      id: Date.now() + '-m',
      role: 'assistant',
      content: mockResponses[question] || 'He thong dang ban. Vui long thu lai sau.',
      created_at: new Date().toISOString(),
      is_mock: true,
    }])
    setLoading(false)
  }

  const useQuickPrompt = (question) => {
    setInput(question)
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
        className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all flex items-center justify-center text-2xl z-50"
      >
        {open ? '✕' : '💬'}
      </button>

      {/* Chat window */}
      {open && (
        <div className="fixed z-50 bottom-20 left-2 right-2 sm:bottom-24 sm:left-auto sm:right-6 sm:w-[390px] h-[min(76dvh,620px)] max-h-[calc(100dvh-5.5rem)] bg-white rounded-2xl shadow-2xl border flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-3 rounded-t-2xl flex items-center justify-between">
            <div>
              <p className="font-semibold text-sm">Trợ lý SDS</p>
              <p className="text-xs opacity-80">Hỗ trợ 24/7</p>
            </div>
            <button onClick={escalate} className="text-xs bg-white/20 px-2 py-1 rounded-lg hover:bg-white/30">
              👤 Nhân viên
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-slate-50/60">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[90%] sm:max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-sm'
                      : msg.role === 'staff'
                      ? 'bg-orange-50 text-orange-800 border border-orange-200 rounded-bl-sm'
                      : msg.is_mock
                      ? 'bg-amber-50 text-amber-800 border border-amber-200 rounded-bl-sm'
                      : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                  }`}>
                    {msg.content}
                    {msg.is_mock && <span className="text-xs opacity-60 block mt-1">Mock response</span>}
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

          {!loading && suggestedQuestions.length === 0 && messages.length <= 2 && (
            <div className="px-3 py-2 border-t bg-white">
              <p className="text-[11px] text-gray-500 mb-2">Gợi ý nhanh</p>
              <div className="flex flex-wrap gap-1.5">
                {quickPrompts.map((q) => (
                  <button
                    key={q}
                    onClick={() => useQuickPrompt(q)}
                    className="text-xs bg-blue-50 border border-blue-200 text-blue-700 rounded-full px-2.5 py-1 hover:bg-blue-100"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {suggestedQuestions.length > 0 && (
            <div className="px-3 py-2 border-t bg-blue-50 space-y-1">
              <p className="text-xs text-gray-600 font-semibold mb-1">Cau hoi thuong gap:</p>
              {suggestedQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => selectSuggestedQuestion(q)}
                  className="w-full text-left text-xs bg-white border border-blue-200 rounded-lg px-2 py-1.5 hover:bg-blue-100 transition-colors text-gray-700"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t flex gap-2 bg-white">
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
