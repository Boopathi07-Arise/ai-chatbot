const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

/**
 * Sends a message to the ASHURA backend (Grok API) and returns the response.
 * @param {string} message - The user's message
 * @param {string|null} conversationId - Optional conversation ID
 * @returns {Promise<{ response: string, conversation_id: string } | { error: string }>}
 */
export async function sendMessage(message, conversationId = null) {
  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    })

    if (!res.ok) {
      const err = await res.json()
      return { error: err.detail || 'Server error. Please try again.' }
    }

    const data = await res.json()
    return { response: data.response, conversation_id: data.conversation_id }
  } catch {
    return { error: 'Unable to reach the server. Make sure your backend is running.' }
  }
}