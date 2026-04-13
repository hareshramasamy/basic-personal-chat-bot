import React, { useState, useEffect, useRef } from 'react'
import api from '../api.js'

const PRIMARY = '#c8102f'

function StatusBadge({ status }) {
  const s = (status || '').toLowerCase()
  let bg, color
  if (s === 'ready') { bg = '#e6f9ed'; color = '#1a7a3c' }
  else if (s === 'failed') { bg = '#fff0f0'; color = PRIMARY }
  else { bg = '#fffbe6'; color = '#8a6d00' }

  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 12,
      fontSize: 12,
      fontWeight: 600,
      background: bg,
      color,
      textTransform: 'capitalize',
    }}>
      {s === 'processing' ? 'Processing' : s === 'ready' ? 'Ready' : s === 'failed' ? 'Failed' : status}
    </span>
  )
}

export default function KnowledgeSources() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(null)
  const intervalRef = useRef(null)
  const userId = localStorage.getItem('avatar_user_id')

  async function fetchDocs() {
    try {
      const res = await api.get(`/users/${userId}/documents`)
      setDocs(res.data.documents || [])
    } catch (err) {
      setError('Failed to load documents.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocs()
  }, [])

  useEffect(() => {
    const hasProcessing = docs.some(d => (d.status || '').toLowerCase() === 'processing')
    if (hasProcessing) {
      if (!intervalRef.current) {
        intervalRef.current = setInterval(fetchDocs, 3000)
      }
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [docs])

  async function handleDelete(docId) {
    setDeleting(docId)
    try {
      await api.delete(`/users/${userId}/documents/${docId}`)
      setDocs(prev => prev.filter(d => d.doc_id !== docId))
    } catch (err) {
      alert('Failed to delete document.')
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div>
      <h2 style={styles.heading}>Knowledge Sources</h2>
      <p style={styles.sub}>Documents and content your AI avatar uses to answer questions.</p>

      {loading && <p style={styles.muted}>Loading…</p>}
      {error && <p style={{ color: PRIMARY }}>{error}</p>}

      {!loading && docs.length === 0 && (
        <div style={styles.empty}>
          No documents yet. Go to <strong>Add Source</strong> to upload content.
        </div>
      )}

      {!loading && docs.length > 0 && (
        <div style={styles.tableWrap}>
          <table style={styles.table}>
            <thead>
              <tr>
                {['Filename', 'Type', 'Uploaded', 'Status', ''].map(h => (
                  <th key={h} style={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {docs.map(doc => (
                <tr key={doc.id} style={styles.tr}>
                  <td style={styles.td}>
                    <span style={styles.filename}>{doc.filename || doc.name || '—'}</span>
                  </td>
                  <td style={styles.td}>
                    <span style={{
                      ...styles.type,
                      ...(( doc.source_type || doc.type) === 'visitor_answer'
                        ? { background: '#e8f4fd', color: '#1a6fa8' }
                        : {})
                    }}>
                      {doc.source_type === 'visitor_answer' ? 'Visitor Q'
                        : doc.type || doc.source_type || '—'}
                    </span>
                  </td>
                  <td style={styles.td}>
                    {doc.uploaded_at
                      ? new Date(doc.uploaded_at).toLocaleDateString()
                      : '—'}
                  </td>
                  <td style={styles.td}>
                    <StatusBadge status={doc.status || 'processing'} />
                  </td>
                  <td style={{ ...styles.td, textAlign: 'right' }}>
                    <button
                      onClick={() => handleDelete(doc.doc_id)}
                      disabled={deleting === doc.doc_id}
                      style={styles.deleteBtn}
                    >
                      {deleting === doc.doc_id ? 'Deleting…' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

const styles = {
  heading: { fontSize: 22, fontWeight: 700, color: '#111', margin: '0 0 6px' },
  sub: { color: '#666', fontSize: 14, marginTop: 0, marginBottom: 24 },
  muted: { color: '#999', fontSize: 14 },
  empty: {
    background: '#fff',
    border: '1px solid #e8e8e8',
    borderRadius: 8,
    padding: '32px',
    textAlign: 'center',
    color: '#666',
    fontSize: 14,
  },
  tableWrap: {
    background: '#fff',
    borderRadius: 8,
    border: '1px solid #e8e8e8',
    overflow: 'hidden',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 14,
  },
  th: {
    background: '#fafafa',
    padding: '11px 16px',
    textAlign: 'left',
    fontSize: 12,
    fontWeight: 600,
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    borderBottom: '1px solid #eee',
  },
  tr: {
    borderBottom: '1px solid #f0f0f0',
  },
  td: {
    padding: '13px 16px',
    color: '#333',
    verticalAlign: 'middle',
  },
  filename: {
    fontWeight: 500,
    color: '#111',
  },
  type: {
    background: '#f0f0f0',
    padding: '2px 8px',
    borderRadius: 4,
    fontSize: 12,
    color: '#555',
  },
  deleteBtn: {
    background: 'none',
    border: '1px solid #ddd',
    color: '#888',
    padding: '5px 12px',
    borderRadius: 4,
    cursor: 'pointer',
    fontSize: 13,
  },
}
