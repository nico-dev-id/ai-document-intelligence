'use client'

import { useState } from 'react'

const API = 'http://localhost:8000'

export default function Register() {
  const [nama, setNama] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [pesan, setPesan] = useState('')
  const [loading, setLoading] = useState(false)

  const handleRegister = async () => {
    if (!nama || !email || !password) {
      setPesan('Semua field wajib diisi!')
      return
    }
    setLoading(true)
    const res = await fetch(`${API}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nama, email, password })
    })
    const data = await res.json()
    setLoading(false)

    if (res.ok) {
      setPesan('✅ Registrasi berhasil! Mengarahkan ke login...')
      setTimeout(() => window.location.href = '/login', 1500)
    } else {
      setPesan(data.detail || 'Registrasi gagal!')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-2xl shadow-lg w-96">
        <div className="text-center mb-8">
          <div className="text-4xl mb-2">🤖</div>
          <h1 className="text-3xl font-bold text-indigo-600">Nico DocAI</h1>
          <p className="text-gray-500 mt-1 text-sm">Buat akun baru</p>
        </div>

        <input
          type="text"
          placeholder="Nama lengkap"
          value={nama}
          onChange={(e) => setNama(e.target.value)}
          className="w-full border border-gray-300 p-3 rounded-lg mb-3 focus:outline-none focus:border-indigo-500 text-gray-800"
        />

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-gray-300 p-3 rounded-lg mb-3 focus:outline-none focus:border-indigo-500 text-gray-800"
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleRegister()}
          className="w-full border border-gray-300 p-3 rounded-lg mb-4 focus:outline-none focus:border-indigo-500 text-gray-800"
        />

        {pesan && (
          <p className={`text-sm mb-4 ${pesan.includes('✅') ? 'text-green-600' : 'text-red-500'}`}>
            {pesan}
          </p>
        )}

        <button
          onClick={handleRegister}
          disabled={loading}
          className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium transition"
        >
          {loading ? 'Mendaftar...' : 'Daftar'}
        </button>

        <p className="text-center text-sm mt-4 text-gray-600">
          Sudah punya akun?{' '}
          <a href="/login" className="text-indigo-600 font-medium hover:underline">
            Masuk
          </a>
        </p>
      </div>
    </div>
  )
}