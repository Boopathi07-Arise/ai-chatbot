import { useState } from 'react'
import ChatWindow from '../components/ChatWindow'
import ChatInput from '../components/ChatInput'
import { sendMessage } from '../services/api'

export default function ChatPage() {
    const [messages, setMessages] = useState([
        { text: "Hello! I'm ASHURA, your AI assistant. How can I help you today?", sender: 'bot', timestamp: new Date() },
    ])
    const [loading, setLoading] = useState(false)
    const [conversationId, setConversationId] = useState(null)

    const handleSend = async (text) => {
        setMessages(prev => [...prev, { text, sender: 'user', timestamp: new Date() }])
        setLoading(true)
        const result = await sendMessage(text, conversationId)
        setLoading(false)
        if (result.error) {
            setMessages(prev => [...prev, { text: result.error, sender: 'bot', timestamp: new Date() }])
        } else {
            if (result.conversation_id) setConversationId(result.conversation_id)
            setMessages(prev => [...prev, { text: result.response, sender: 'bot', timestamp: new Date() }])
        }
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#212121' }}>

            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 20px', background: '#171717', borderBottom: '1px solid #2a2a2a', flexShrink: 0 }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#0d0000', border: '1.5px solid #cc0000', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <svg width="22" height="22" viewBox="0 0 40 40" fill="none">
                        <line x1="8" y1="3" x2="27" y2="37" stroke="#cc0000" strokeWidth="2.2" strokeLinecap="round" />
                        <rect x="4" y="1" width="8" height="3" rx="1" fill="#8a0000" transform="rotate(-30 8 3)" />
                        <rect x="10" y="29" width="5" height="4" rx="0.5" fill="#5a2000" transform="rotate(-30 12 31)" />
                        <line x1="32" y1="3" x2="13" y2="37" stroke="#cc0000" strokeWidth="2.2" strokeLinecap="round" />
                        <rect x="28" y="1" width="8" height="3" rx="1" fill="#8a0000" transform="rotate(30 32 3)" />
                        <rect x="25" y="29" width="5" height="4" rx="0.5" fill="#5a2000" transform="rotate(30 28 31)" />
                        <line x1="20" y1="1" x2="20" y2="39" stroke="#ff2200" strokeWidth="2.8" strokeLinecap="round" />
                        <rect x="14" y="22" width="12" height="3.5" rx="1" fill="#8a0000" />
                        <rect x="17" y="25.5" width="6" height="5" rx="0.5" fill="#5a2000" />
                        <circle cx="20" cy="2" r="2" fill="#ff4400" opacity="0.7" />
                    </svg>
                </div>
                <div>
                    <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: '22px', letterSpacing: '5px', color: '#fff', lineHeight: 1 }}>ASHURA</div>
                    <div style={{ fontSize: '11px', color: '#555', marginTop: '3px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22aa44', display: 'inline-block' }} />
                        Online
                    </div>
                </div>
            </div>

            <ChatWindow messages={messages} loading={loading} />
            <ChatInput onSend={handleSend} disabled={loading} />
        </div>
    )
}