'use client'

import { useEffect } from "react"

export default function Home() {
  useEffect(() => {
    window.location.href = '/login'
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-indigo-50">
      <p className="text-indigo-600">Loading...</p>
    </div>
  )
}