'use client'

import { useState } from 'react'

const API = 'https://nico-dev-id-ai-document-intelligence-api.hf.space'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [pesan, setPesan] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async () => {
    if (!email || !password) {
      setPesan('Email dan password wajib diisi!')
      return
    }
    setLoading(true)
    setPesan('Menghubungkan ke server...')

    try {
      const response = await fetch(`${API}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${email}&password=${password}`
      })

      if (!response.ok) {
        const data = await response.json()
        setPesan(data.detail || 'Login gagal!')
        setLoading(false)
        return
      }

      const data = await response.json()
      setLoading(false)
      localStorage.setItem('token', data.access_token)
      window.location.href = '/dashboard'

    } catch (error) {
      setPesan('Server sedang starting up, tunggu 1-2 menit dan coba lagi! 🚀')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-2xl shadow-lg w-96">
        <div className="text-center mb-8">
          <div className="text-4xl mb-2">🤖</div>
          <h1 className="text-3xl font-bold text-indigo-600">Nico DocAI</h1>
          <p className="text-gray-500 mt-1 text-sm">AI Document Intelligence</p>
        </div>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
          className="w-full border border-gray-300 p-3 rounded-lg mb-3 focus:outline-none focus:border-indigo-500 text-gray-800"
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
          className="w-full border border-gray-300 p-3 rounded-lg mb-4 focus:outline-none focus:border-indigo-500 text-gray-800"
        />

        {pesan && (
          <p className={`text-sm mb-4 ${pesan.includes('🚀') ? 'text-blue-500' : pesan.includes('Menghubungkan') ? 'text-gray-500' : 'text-red-500'}`}>
            {pesan}
          </p>
        )}

        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium transition"
        >
          {loading ? 'Menghubungkan...' : 'Masuk'}
        </button>

        <p className="text-center text-sm mt-4 text-gray-600">
          Belum punya akun?{' '}
          <a href="/register" className="text-indigo-600 font-medium hover:underline">
            Daftar sekarang
          </a>
        </p>
      </div>
    </div>
  )
}