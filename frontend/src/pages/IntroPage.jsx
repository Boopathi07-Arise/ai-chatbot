import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const KEYFRAMES = `
  @keyframes shootLine {
    0%   { left: -110%; opacity: 0; }
    5%   { opacity: 1; }
    80%  { opacity: 1; }
    100% { left: 110%; opacity: 0; }
  }

  @keyframes slamIn {
    from { opacity: 0; transform: scale(2.5) rotate(-6deg); }
    to   { opacity: 1; transform: scale(1) rotate(0deg); }
  }

  @keyframes blinkHint {
    0%, 100% { opacity: 0.2; }
    50%       { opacity: 0; }
  }
`

export default function IntroPage() {
    const navigate = useNavigate()

    /* 5 seconds total */
    useEffect(() => {
        const t = setTimeout(() => navigate('/chat'), 5000)
        return () => clearTimeout(t)
    }, [navigate])

    return (
        <>
            <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Black+Ops+One&family=Bebas+Neue&display=swap');
        ${KEYFRAMES}
      `}</style>

            {/* ── Full screen black bg ── */}
            <div style={styles.page}>

                {/* Red radial glow */}
                <div style={styles.glow} />

                {/* ══════════════════════════
            Z SLASH LINES
            1. Top bar    → 0.1s
            2. Diagonal   → 0.7s
            3. Bottom bar → 1.3s
            4. ASHURA     → 1.9s
        ══════════════════════════ */}
                <div style={styles.slashContainer}>

                    {/* TOP BAR glow + line */}
                    <div style={{ ...styles.zline, ...styles.topGlow }} />
                    <div style={{ ...styles.zline, ...styles.topLine }} />

                    {/* DIAGONAL glow + line */}
                    <div style={{ ...styles.zline, ...styles.diagGlow }} />
                    <div style={{ ...styles.zline, ...styles.diagLine }} />

                    {/* BOTTOM BAR glow + line */}
                    <div style={{ ...styles.zline, ...styles.botGlow }} />
                    <div style={{ ...styles.zline, ...styles.botLine }} />

                </div>

                {/* ── ASHURA slams in after all 3 lines ── */}
                <div style={styles.centre}>
                    <div style={styles.name}>ASHURA</div>
                    <div style={styles.hint}>— ENTERING ASHURA —</div>
                </div>

            </div>
        </>
    )
}

/* ── Shared base for all slash lines ── */
const base = {
    position: 'absolute',
    left: '-110%',
    opacity: 0,
}

const styles = {
    page: {
        position: 'fixed',
        inset: 0,
        background: '#000000',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
    },

    glow: {
        position: 'absolute',
        inset: 0,
        background: 'radial-gradient(ellipse 75% 60% at 50% 50%, #1a0000 0%, #000 65%)',
        pointerEvents: 'none',
    },

    slashContainer: {
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
    },

    /* base for all lines */
    zline: base,

    /* ── TOP BAR ── */
    topLine: {
        top: '28%',
        width: '95%',
        height: '8px',
        borderRadius: '3px',
        background: 'linear-gradient(90deg, transparent 0%, #cc1500 10%, #ff5500 30%, #ffdd00 50%, #ff5500 70%, #cc1500 85%, transparent 100%)',
        animation: 'shootLine 0.7s cubic-bezier(0.1,0.6,0.3,1) 0.1s forwards',
    },
    topGlow: {
        top: 'calc(28% - 8px)',
        width: '95%',
        height: '24px',
        borderRadius: '12px',
        background: 'linear-gradient(90deg, transparent, #ff3300 20%, #ffaa00 50%, transparent)',
        filter: 'blur(6px)',
        animation: 'shootLine 0.7s cubic-bezier(0.1,0.6,0.3,1) 0.1s forwards',
    },

    /* ── DIAGONAL ── */
    diagLine: {
        top: '22%',
        width: '110%',
        height: '10px',
        borderRadius: '3px',
        background: 'linear-gradient(90deg, transparent 0%, #cc1500 8%, #ff5500 28%, #ffee00 50%, #ff5500 72%, #cc1500 88%, transparent 100%)',
        transform: 'rotate(22deg)',
        transformOrigin: 'left center',
        animation: 'shootLine 0.8s cubic-bezier(0.1,0.6,0.3,1) 0.7s forwards',
    },
    diagGlow: {
        top: 'calc(22% - 10px)',
        width: '110%',
        height: '30px',
        borderRadius: '15px',
        background: 'linear-gradient(90deg, transparent, #ff3300 15%, #ffcc00 50%, transparent)',
        filter: 'blur(8px)',
        transform: 'rotate(22deg)',
        transformOrigin: 'left center',
        animation: 'shootLine 0.8s cubic-bezier(0.1,0.6,0.3,1) 0.7s forwards',
    },

    /* ── BOTTOM BAR ── */
    botLine: {
        top: '68%',
        width: '95%',
        height: '8px',
        borderRadius: '3px',
        background: 'linear-gradient(90deg, transparent 0%, #cc1500 10%, #ff5500 30%, #ffdd00 50%, #ff5500 70%, #cc1500 85%, transparent 100%)',
        animation: 'shootLine 0.7s cubic-bezier(0.1,0.6,0.3,1) 1.3s forwards',
    },
    botGlow: {
        top: 'calc(68% - 8px)',
        width: '95%',
        height: '24px',
        borderRadius: '12px',
        background: 'linear-gradient(90deg, transparent, #ff3300 20%, #ffaa00 50%, transparent)',
        filter: 'blur(6px)',
        animation: 'shootLine 0.7s cubic-bezier(0.1,0.6,0.3,1) 1.3s forwards',
    },

    /* ── ASHURA text (appears after all 3 lines at 1.9s) ── */
    centre: {
        position: 'relative',
        zIndex: 10,
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        opacity: 0,
        animation: 'slamIn 0.55s cubic-bezier(0.34,1.4,0.64,1) 1.9s forwards',
    },

    name: {
        fontFamily: "'Black Ops One', sans-serif",
        fontSize: 'clamp(52px, 13vw, 130px)',
        color: '#cc0000',
        letterSpacing: '6px',
        lineHeight: 1,
        textShadow: '3px 3px 0 #550000, 0 0 30px #ff0000, 0 0 80px #880000',
    },

    hint: {
        fontFamily: "'Bebas Neue', sans-serif",
        fontSize: '12px',
        letterSpacing: '5px',
        color: 'rgba(255,255,255,0.2)',
        marginTop: '36px',
        animation: 'blinkHint 1.4s ease 2.8s infinite',
    },
}