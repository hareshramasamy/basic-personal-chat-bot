(function () {
  const script = document.currentScript
  const token = script.getAttribute('data-token')
  const apiUrl = script.getAttribute('data-api') || 'https://your-api.app-runner.aws'

  if (!token) {
    console.error('Avatar widget: missing data-token attribute')
    return
  }

  const style = document.createElement('style')
  style.textContent = `
    #avatar-bubble { position: fixed; bottom: 24px; right: 24px; width: 56px; height: 56px;
      border-radius: 50%; background: #c8102f; cursor: pointer; display: flex;
      align-items: center; justify-content: center; color: white; font-size: 24px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 9999; }
    #avatar-panel { position: fixed; bottom: 96px; right: 24px; width: 340px; height: 480px;
      background: white; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.15);
      display: none; flex-direction: column; z-index: 9999; overflow: hidden; }
    #avatar-resize-top { position: absolute; top: 0; left: 8px; right: 8px; height: 6px; cursor: n-resize; z-index: 10; }
    #avatar-resize-left { position: absolute; left: 0; top: 8px; bottom: 8px; width: 6px; cursor: w-resize; z-index: 10; }
    #avatar-resize-corner { position: absolute; top: 0; left: 0; width: 12px; height: 12px; cursor: nw-resize; z-index: 11; }
    #avatar-panel.open { display: flex; }
    #avatar-header { display: flex; align-items: center; justify-content: space-between;
      padding: 12px 16px; background: #c8102f; color: white; font-family: sans-serif;
      font-size: 14px; font-weight: 600; flex-shrink: 0; }
    #avatar-clear { background: none; border: none; color: white; font-size: 18px;
      cursor: pointer; opacity: 0.8; line-height: 1; padding: 0; }
    #avatar-clear:hover { opacity: 1; }
    #avatar-messages { flex: 1; overflow-y: auto; padding: 16px; font-family: sans-serif; font-size: 14px; }
    .avatar-msg { margin: 8px 0; padding: 8px 12px; border-radius: 8px; max-width: 80%; }
    .avatar-msg.user { display: inline-block; }
    .avatar-msg-row { display: flex; }
    .avatar-msg-row.user { justify-content: flex-end; }
    .avatar-msg.user { background: #c8102f; color: white; }
    .avatar-msg.bot { background: #f3f4f6; }
    .avatar-msg.error { background: #fee2e2; color: #991b1b; }
    .avatar-msg.typing { display: flex; gap: 4px; align-items: center; padding: 12px 14px; }
    .dot { width: 7px; height: 7px; border-radius: 50%; background: #9ca3af; animation: blink 1.2s infinite; }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink { 0%,80%,100% { opacity: 0.2; } 40% { opacity: 1; } }
    #avatar-input-row { display: flex; padding: 8px; border-top: 1px solid #e5e7eb; flex-shrink: 0; }
    #avatar-input { flex: 1; padding: 8px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; }
    #avatar-send { margin-left: 8px; padding: 8px 14px; background: #c8102f; color: white;
      border: none; border-radius: 6px; cursor: pointer; }
    .avatar-msg p { margin: 0 0 6px 0; }
    .avatar-msg p:last-child { margin-bottom: 0; }
    .avatar-msg ul { margin: 4px 0; padding-left: 18px; }
    .avatar-msg li { margin: 3px 0; }
  `
  document.head.appendChild(style)

  document.body.insertAdjacentHTML('beforeend', `
    <div id="avatar-bubble">💬</div>
    <div id="avatar-panel">
      <div id="avatar-resize-top"></div>
      <div id="avatar-resize-left"></div>
      <div id="avatar-resize-corner"></div>
      <div id="avatar-header">
        <span>AI Avatar</span>
        <button id="avatar-clear" title="Clear chat">↺</button>
      </div>
      <div id="avatar-messages"></div>
      <div id="avatar-input-row">
        <input id="avatar-input" type="text" placeholder="Ask me anything..." />
        <button id="avatar-send">Send</button>
      </div>
    </div>
  `)

  const bubble = document.getElementById('avatar-bubble')
  const panel = document.getElementById('avatar-panel')
  const messages = document.getElementById('avatar-messages')
  const input = document.getElementById('avatar-input')
  const sendBtn = document.getElementById('avatar-send')
  const clearBtn = document.getElementById('avatar-clear')
  let history = []

  bubble.addEventListener('click', () => panel.classList.toggle('open'))

  clearBtn.addEventListener('click', () => {
    messages.innerHTML = ''
    history = []
  })

  function addTypingIndicator() {
    messages.insertAdjacentHTML('beforeend', `
      <div class="avatar-msg-row" id="avatar-typing">
        <div class="avatar-msg bot typing">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    `)
    messages.scrollTop = messages.scrollHeight
  }

  function removeTypingIndicator() {
    const el = document.getElementById('avatar-typing')
    if (el) el.remove()
  }

  function renderMarkdown(text) {
    const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    const lines = escaped.split('\n')
    const result = []
    let inList = false
    for (const line of lines) {
      const bullet = line.match(/^[-*]\s+(.+)/)
      if (bullet) {
        if (!inList) { result.push('<ul>'); inList = true }
        result.push(`<li>${bullet[1]}</li>`)
      } else {
        if (inList) { result.push('</ul>'); inList = false }
        if (line.trim()) result.push(`<p>${line}</p>`)
      }
    }
    if (inList) result.push('</ul>')
    return result.join('')
  }

  function addBotMessage(text, isError = false) {
    const html = isError ? text : renderMarkdown(text)
    messages.insertAdjacentHTML('beforeend', `<div class="avatar-msg-row"><div class="avatar-msg bot${isError ? ' error' : ''}">${html}</div></div>`)
    messages.scrollTop = messages.scrollHeight
  }

  async function sendMessage() {
    const text = input.value.trim()
    if (!text) return
    input.value = ''
    input.disabled = true
    sendBtn.disabled = true

    messages.insertAdjacentHTML('beforeend', `<div class="avatar-msg-row user"><div class="avatar-msg user">${text}</div></div>`)
    messages.scrollTop = messages.scrollHeight

    addTypingIndicator()

    try {
      const res = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ embed_token: token, message: text, history })
      })

      removeTypingIndicator()

      if (!res.ok) {
        addBotMessage(`Error ${res.status}: something went wrong. Please try again.`, true)
        return
      }

      const data = await res.json()
      addBotMessage(data.response)

      history.push({ role: 'user', content: text })
      history.push({ role: 'assistant', content: data.response })
    } catch (err) {
      removeTypingIndicator()
      addBotMessage('Could not reach the server. Please check your connection and try again.', true)
    } finally {
      input.disabled = false
      sendBtn.disabled = false
      input.focus()
    }
  }

  function makeResizable(handle, resizeTop, resizeLeft) {
    handle.addEventListener('mousedown', e => {
      e.preventDefault()
      const startX = e.clientX, startY = e.clientY
      const startW = panel.offsetWidth, startH = panel.offsetHeight
      function onMove(e) {
        if (resizeLeft) {
          const newW = Math.max(280, startW - (e.clientX - startX))
          panel.style.width = newW + 'px'
        }
        if (resizeTop) {
          const newH = Math.max(360, startH - (e.clientY - startY))
          panel.style.height = newH + 'px'
        }
      }
      function onUp() {
        document.removeEventListener('mousemove', onMove)
        document.removeEventListener('mouseup', onUp)
      }
      document.addEventListener('mousemove', onMove)
      document.addEventListener('mouseup', onUp)
    })
  }

  makeResizable(document.getElementById('avatar-resize-top'), true, false)
  makeResizable(document.getElementById('avatar-resize-left'), false, true)
  makeResizable(document.getElementById('avatar-resize-corner'), true, true)

  sendBtn.addEventListener('click', sendMessage)
  input.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage() })
})()
