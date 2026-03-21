export default function MessageBubble({ text, sender }) {
    const isAI = sender === 'bot'

    return (
        <div style={{ ...styles.row, background: isAI ? '#2a2a2a' : 'transparent' }}>
            <div style={styles.inner}>
                <div style={{
                    ...styles.avatar,
                    background: isAI ? '#0d0000' : '#2a2a2a',
                    border: isAI ? '1px solid #cc0000' : '1px solid #444',
                }}>
                    {isAI ? (
                        <svg width="18" height="18" viewBox="0 0 40 40" fill="none">
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
                    ) : (
                        <span style={{ fontSize: '12px', color: '#777', fontFamily: 'Inter, sans-serif' }}>U</span>
                    )}
                </div>
                <div style={styles.body}>
                    <div style={{ ...styles.sender, color: isAI ? '#aaa' : '#666' }}>
                        {isAI ? 'Ashura' : 'You'}
                    </div>
                    <div style={styles.text}>{text}</div>
                </div>
            </div>
        </div>
    )
}

const styles = {
    row: { width: '100%', padding: '6px 0', animation: 'msgFade 0.25s ease both' },
    inner: { maxWidth: '720px', margin: '0 auto', padding: '12px 24px', display: 'flex', gap: '14px', alignItems: 'flex-start' },
    avatar: { width: '30px', height: '30px', borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '2px' },
    body: { flex: 1, minWidth: 0 },
    sender: { fontSize: '12px', fontWeight: 500, marginBottom: '6px' },
    text: { fontSize: '15px', lineHeight: 1.75, color: '#ececec', whiteSpace: 'pre-wrap', wordBreak: 'break-word' },
}