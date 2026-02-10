import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl">🎨</span>
            <span className="text-xl font-bold">Gemini Image Chat</span>
          </Link>
          <nav className="flex items-center space-x-4">
            <Link
              to="/"
              className="px-3 py-1.5 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors"
            >
              세션 목록
            </Link>
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  )
}
