'use client'

import { useState, useEffect } from 'react'

const API = 'https://nico-dev-id-ai-document-intelligence-api.hf.space'

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [dokumen, setDokumen] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [pesan, setPesan] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      window.location.href = '/login'
      return
    }
    ambilProfil(token)
    ambilDokumen(token)
  }, [])

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

  const uploadDokumen = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
      setPesan('Hanya file PDF dan TXT!')
      return
    }

    setUploading(true)
    setPesan('')
    const token = localStorage.getItem('token')
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(`${API}/documents/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    })

    const data = await res.json()
    setUploading(false)

    if (res.ok) {
      setPesan('✅ Dokumen berhasil diupload!')
      ambilDokumen(token)
    } else {
      setPesan(data.detail || 'Upload gagal!')
    }
  }

  const hapusDokumen = async (id, nama) => {
    if (!confirm(`Hapus dokumen "${nama}"?`)) return
    const token = localStorage.getItem('token')
    await fetch(`${API}/documents/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    ambilDokumen(token)
  }

  const logout = () => {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-indigo-600 text-white px-6 py-4 flex justify-between items-center shadow">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🤖</span>
          <span className="text-xl font-bold">DocAI</span>
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

      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Dokumen Saya</h2>
          <p className="text-gray-500 text-sm mt-1">Upload dokumen PDF atau TXT untuk dianalisis AI</p>
        </div>

        {/* Upload Area */}
        <div className="bg-white rounded-2xl shadow p-6 mb-6">
          <label className="flex flex-col items-center justify-center border-2 border-dashed border-indigo-300 rounded-xl p-8 cursor-pointer hover:bg-indigo-50 transition">
            <span className="text-4xl mb-3">📄</span>
            <span className="text-indigo-600 font-medium">
              {uploading ? 'Mengupload...' : 'Klik untuk upload dokumen'}
            </span>
            <span className="text-gray-400 text-sm mt-1">PDF atau TXT</span>
            <input
              type="file"
              accept=".pdf,.txt"
              onChange={uploadDokumen}
              className="hidden"
              disabled={uploading}
            />
          </label>
          {pesan && (
            <p className={`text-center mt-3 text-sm ${pesan.includes('✅') ? 'text-green-600' : 'text-red-500'}`}>
              {pesan}
            </p>
          )}
        </div>

        {/* Tombol Chat */}
        {dokumen.length > 0 && (
          <div className="mb-6">
            <a
              href="/chat"
              className="inline-flex items-center gap-2 bg-indigo-600 text-white px-6 py-3 rounded-xl hover:bg-indigo-700 font-medium transition"
            >
              <span>💬</span>
              Tanya AI tentang dokumen kamu
            </a>
          </div>
        )}
        <a href=""></a>

        {/* List Dokumen */}
        {dokumen.length === 0 ? (
          <div className="bg-white rounded-2xl shadow p-12 text-center">
            <div className="text-5xl mb-4">📂</div>
            <p className="text-gray-500">Belum ada dokumen. Upload sekarang!</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {dokumen.map((doc) => (
              <div key={doc.id} className="bg-white rounded-2xl shadow p-5 flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div className="text-3xl">
                    {doc.nama_file.endsWith('.pdf') ? '📕' : '📄'}
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">{doc.nama_file}</p>
                    <p className="text-gray-400 text-sm">
                      {new Date(doc.created_at).toLocaleDateString('id-ID')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => hapusDokumen(doc.id, doc.nama_file)}
                  className="text-red-400 hover:text-red-600 px-3 py-1.5 rounded-lg hover:bg-red-50 transition text-sm"
                >
                  Hapus
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}