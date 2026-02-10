import { Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import SessionsPage from './pages/SessionsPage'
import Layout from './components/Layout'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<SessionsPage />} />
        <Route path="/chat/:sessionId" element={<ChatPage />} />
      </Routes>
    </Layout>
  )
}

export default App
