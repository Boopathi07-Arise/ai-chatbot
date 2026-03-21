import { useState, useRef, useEffect } from 'react'

export default function ChatInput({ onSend, disabled }) {
    const [value, setValue] = useState('')
    const textareaRef = useRef(null)

    useEffect(() => {
        const el = textareaRef.current
        if (el) {
            el.style.height = 'auto'
            el.style.height = Math.min(el.scrollHeight, 160) + 'px'
        }
    }, [value])

    const handleSend = () => {
        const trimmed = value.trim()
        if (!trimmed || disabled) return
        onSend(trimmed)
        setValue('')
    }

    const handleKey = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div style={{ padding: '12px 16px 16px', background: '#212121', flexShrink: 0 }}>
            <div style={{ maxWidth: '720px', margin: '0 auto', background: '#2f2f2f', border: '1px solid #3a3a3a', borderRadius: '14px', display: 'flex', alignItems: 'flex-end', gap: '8px', padding: '10px 12px' }}>
                <textarea
                    ref={textareaRef}
                    rows={1}
                    value={value}
                    onChange={e => setValue(e.target.value)}
                    onKeyDown={handleKey}
                    placeholder="Message Ashura..."
                    disabled={disabled}
                    style={{ flex: 1, background: 'transparent', resize: 'none', color: '#ececec', fontSize: '15px', lineHeight: 1.6, minHeight: '26px', maxHeight: '160px', caretColor: '#fff', padding: 0, border: 'none', outline: 'none', fontFamily: 'Inter, sans-serif' }}
                />
                <button
                    onClick={handleSend}
                    disabled={disabled || !value.trim()}
                    style={{ width: '34px', height: '34px', borderRadius: '8px', border: 'none', cursor: disabled || !value.trim() ? 'not-allowed' : 'pointer', background: disabled || !value.trim() ? '#3a1010' : '#cc0000', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, transition: 'background 0.15s' }}
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13" />
                        <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                </button>
            </div>
            <div style={{ maxWidth: '720px', margin: '8px auto 0', fontSize: '11px', color: '#3a3a3a', textAlign: 'center' }}>
                Enter to send · Shift+Enter for new line
            </div>
        </div>
    )
}