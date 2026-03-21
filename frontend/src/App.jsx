import { Routes, Route } from 'react-router-dom'
import IntroPage from './pages/IntroPage'
import ChatPage from './pages/ChatPage'

export default function App() {
    return (
        <Routes>
            <Route path="/" element={<IntroPage />} />
            <Route path="/chat" element={<ChatPage />} />
        </Routes>
    )
}