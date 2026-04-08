import React, { useState } from 'react'
import api from '../api.js'

const PRIMARY = '#c8102f'

export default function EmbedSnippet() {
  const userId = localStorage.getItem('avatar_user_id')
  const [embedToken, setEmbedToken] = useState(localStorage.getItem('avatar_embed_token') || '')
  const [copied, setCopied] = useState(false)
  const [regenerating, setRegenerating] = useState(false)

  const widgetUrl = import.meta.env.VITE_WIDGET_URL || 'https://your-cdn.com/widget.iife.js'
  const apiUrl = import.meta.env.VITE_API_URL || 'https://your-api.com'
  const snippet = embedToken
    ? `<script\n  src="${widgetUrl}"\n  data-token="${embedToken}"\n  data-api="${apiUrl}">\n</script>`
    : '<!-- Regenerate your embed token to see the snippet -->'

  async function handleCopy() {
    if (!embedToken) return
    try {
      await navigator.clipboard.writeText(snippet)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      const el = document.createElement('textarea')
      el.value = snippet
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  async function handleRegenerate() {
    setRegenerating(true)
    try {
      const res = await api.post(`/users/${userId}/regenerate-token`)
      const token = res.data.embed_token
      setEmbedToken(token)
      localStorage.setItem('avatar_embed_token', token)
    } catch {
      alert('Failed to regenerate token.')
    } finally {
      setRegenerating(false)
    }
  }

  return (
    <div>
      <h2 style={styles.heading}>Embed</h2>
      <p style={styles.sub}>
        Copy this snippet and paste it into any HTML page to embed your AI avatar chat widget.
      </p>

      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <span style={styles.cardTitle}>Embed Code</span>
          <button onClick={handleCopy} disabled={!embedToken} style={{ ...styles.copyBtn, background: copied ? '#1a7a3c' : PRIMARY }}>
            {copied ? '✓ Copied!' : 'Copy'}
          </button>
        </div>
        <pre style={styles.pre}>{snippet}</pre>
      </div>

      <div style={styles.infoItem}>
        <div style={styles.infoLabel}>Your Embed Token</div>
        {embedToken ? (
          <code style={styles.infoValue}>{embedToken}</code>
        ) : (
          <span style={{ fontSize: 13, color: '#999' }}>
            Token not available — it's only shown once at signup. Regenerate below to get a new one.
          </span>
        )}
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          style={styles.regenBtn}
        >
          {regenerating ? 'Regenerating…' : 'Regenerate Token'}
        </button>
      </div>

      <div style={styles.instructions}>
        <h3 style={styles.instrTitle}>How to use</h3>
        <ol style={styles.ol}>
          <li>Copy the snippet above.</li>
          <li>Paste it before the closing <code style={styles.code}>&lt;/body&gt;</code> tag of your HTML page.</li>
          <li>The chat widget will appear automatically in the bottom-right corner.</li>
        </ol>
      </div>
    </div>
  )
}

const styles = {
  heading: { fontSize: 22, fontWeight: 700, color: '#111', margin: '0 0 6px' },
  sub: { color: '#666', fontSize: 14, marginTop: 0, marginBottom: 24 },
  card: {
    background: '#1a1a1a',
    borderRadius: 8,
    overflow: 'hidden',
    marginBottom: 20,
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    background: '#222',
    borderBottom: '1px solid #333',
  },
  cardTitle: {
    color: '#aaa',
    fontSize: 12,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  },
  copyBtn: {
    border: 'none',
    color: '#fff',
    padding: '5px 14px',
    borderRadius: 4,
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
  },
  pre: {
    margin: 0,
    padding: '20px',
    color: '#e8e8e8',
    fontSize: 13,
    fontFamily: "'Fira Code', 'Courier New', monospace",
    lineHeight: 1.7,
    overflowX: 'auto',
    whiteSpace: 'pre',
  },
  infoItem: {
    background: '#fff',
    border: '1px solid #e8e8e8',
    borderRadius: 8,
    padding: '16px 20px',
    marginBottom: 20,
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  infoLabel: {
    fontSize: 12,
    fontWeight: 600,
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  infoValue: {
    fontSize: 13,
    color: '#333',
    wordBreak: 'break-all',
    fontFamily: 'monospace',
  },
  regenBtn: {
    alignSelf: 'flex-start',
    marginTop: 4,
    padding: '6px 14px',
    background: 'none',
    border: `1px solid ${PRIMARY}`,
    color: PRIMARY,
    borderRadius: 5,
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
  },
  instructions: {
    background: '#fff',
    border: '1px solid #e8e8e8',
    borderRadius: 8,
    padding: '20px 24px',
  },
  instrTitle: {
    fontSize: 15,
    fontWeight: 600,
    color: '#222',
    margin: '0 0 12px',
  },
  ol: {
    margin: 0,
    paddingLeft: 20,
    color: '#444',
    fontSize: 14,
    lineHeight: 1.9,
  },
  code: {
    background: '#f0f0f0',
    padding: '1px 6px',
    borderRadius: 3,
    fontSize: 13,
    fontFamily: 'monospace',
  },
}
