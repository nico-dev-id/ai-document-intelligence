'use client'

import { useState, useEffect, useRef } from 'react'

const API = 'https://nico-dev-id-ai-document-intelligence-api.hf.space'

export default function Chat() {
  const [user, setUser] = useState(null)
  const [pesan, setPesan] = useState('')
  const [riwayat, setRiwayat] = useState([])
  const [loading, setLoading] = useState(false)
  const [dokumen, setDokumen] = useState([])
  const bottomRef = useRef(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      window.location.href = '/login'
      return
    }
    ambilProfil(token)
    ambilDokumen(token)
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [riwayat])

  const ambilProfil = async (token) => {
    const res = await fetch(`${API}/profil`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return
    }
    const data = await res.json()
    setUser(data)
  }

  const ambilDokumen = async (token) => {
    const res = await fetch(`${API}/documents`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    setDokumen(data.documents || [])
  }

  const kirimPesan = async () => {
    if (!pesan.trim() || loading) return

    if (dokumen.length === 0) {
      alert('Upload dokumen dulu sebelum bertanya!')
      return
    }

    const pesanUser = pesan
    setPesan('')
    setRiwayat(prev => [...prev, { role: 'user', content: pesanUser }])
    setLoading(true)

    const token = localStorage.getItem('token')
    const res = await fetch(`${API}/ask`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ pertanyaan: pesanUser })
    })

    const data = await res.json()
    setLoading(false)

    if (res.ok) {
      setRiwayat(prev => [...prev, {
        role: 'assistant',
        content: data.jawaban,
        sumber: data.sumber
      }])
    } else {
      setRiwayat(prev => [...prev, {
        role: 'assistant',
        content: 'Maaf, terjadi error. Coba lagi!'
      }])
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Navbar */}
      <nav className="bg-indigo-600 text-white px-6 py-4 flex justify-between items-center shadow">
        <div className="flex items-center gap-3">
          <a href="/dashboard" className="text-white hover:text-indigo-200 text-sm">
            ← Kembali
          </a>
          <span className="text-gray-300">|</span>
          <span className="text-2xl">🤖</span>
          <span className="text-xl font-bold">DocAI Chat</span>
        </div>
        <div className="flex items-center gap-4">
          {user && <span className="text-sm">Halo, {user.nama}!</span>}
          <button
            onClick={logout}
            className="bg-white text-indigo-600 px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-indigo-50"
          >
            Logout
          </button>
        </div>
      </nav>

      {/* Info dokumen */}
      <div className="bg-white border-b px-6 py-3">
        <p className="text-sm text-gray-500">
          📚 {dokumen.length} dokumen tersedia:
          {' '}{dokumen.map(d => d.nama_file).join(', ')}
        </p>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full">
        {riwayat.length === 0 && (
          <div className="text-center mt-20">
            <div className="text-6xl mb-4">💬</div>
            <h3 className="text-xl font-bold text-gray-700 mb-2">
              Tanya apapun tentang dokumen kamu!
            </h3>
            <p className="text-gray-400 text-sm">
              AI akan mencari jawaban dari semua dokumen yang sudah diupload
            </p>
          </div>
        )}

        {riwayat.map((chat, index) => (
          <div key={index} className={`mb-4 flex ${chat.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl px-4 py-3 rounded-2xl ${
              chat.role === 'user'
                ? 'bg-indigo-600 text-white rounded-br-none'
                : 'bg-white shadow text-gray-800 rounded-bl-none'
            }`}>
              <p className="text-sm leading-relaxed">{chat.content}</p>
              {chat.sumber && chat.sumber.length > 0 && (
                <p className="text-xs mt-2 opacity-60">
                  📄 Sumber: {chat.sumber.filter(Boolean).join(', ')}
                </p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-white shadow px-4 py-3 rounded-2xl rounded-bl-none">
              <div className="flex gap-1 items-center">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t p-4">
        <div className="max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            placeholder="Tanya tentang dokumen kamu..."
            value={pesan}
            onChange={(e) => setPesan(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && kirimPesan()}
            className="flex-1 border border-gray-300 p-3 rounded-xl focus:outline-none focus:border-indigo-500 text-gray-800"
          />
          <button
            onClick={kirimPesan}
            disabled={loading}
            className="bg-indigo-600 text-white px-6 py-3 rounded-xl hover:bg-indigo-700 disabled:opacity-50 font-medium transition"
          >
            Kirim
          </button>
        </div>
      </div>
    </div>
  )
}