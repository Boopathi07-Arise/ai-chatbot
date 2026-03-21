import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'

const KEYFRAMES = `
  @keyframes msgFade {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes dotBounce {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
    40%            { transform: scale(1.1); opacity: 1; }
  }
`

function TypingIndicator() {
    return (
        <div style={{ width: '100%', padding: '6px 0', background: '#2a2a2a' }}>
            <div style={{ maxWidth: '720px', margin: '0 auto', padding: '12px 24px', display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                <div style={{ width: '30px', height: '30px', borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '2px', background: '#0d0000', border: '1px solid #cc0000' }}>
                    <svg width="18" height="18" viewBox="0 0 40 40" fill="none">
                        <line x1="8" y1="3" x2="27" y2="37" stroke="#cc0000" strokeWidth="2.2" strokeLinecap="round" />
                        <line x1="32" y1="3" x2="13" y2="37" stroke="#cc0000" strokeWidth="2.2" strokeLinecap="round" />
                        <line x1="20" y1="1" x2="20" y2="39" stroke="#ff2200" strokeWidth="2.8" strokeLinecap="round" />
                        <rect x="14" y="22" width="12" height="3.5" rx="1" fill="#8a0000" />
                        <circle cx="20" cy="2" r="2" fill="#ff4400" opacity="0.7" />
                    </svg>
                </div>
                <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '12px', fontWeight: 500, marginBottom: '8px', color: '#aaa' }}>Ashura</div>
                    <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                        {[0, 0.18, 0.36].map((delay, i) => (
                            <span key={i} style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#555', display: 'block', animation: `dotBounce 1.3s ease-in-out ${delay}s infinite` }} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default function ChatWindow({ messages, loading }) {
    const bottomRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, loading])

    return (
        <>
            <style>{KEYFRAMES}</style>
            <div style={{ flex: 1, overflowY: 'auto', paddingTop: '16px', paddingBottom: '8px', scrollbarWidth: 'thin', scrollbarColor: '#333 transparent' }}>
                {messages.map((msg, i) => (
                    <MessageBubble key={i} text={msg.text} sender={msg.sender} />
                ))}
                {loading && <TypingIndicator />}
                <div ref={bottomRef} />
            </div>
        </>
    )
}