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
      border-radius: 50%; background: #4f46e5; cursor: pointer; display: flex;
      align-items: center; justify-content: center; color: white; font-size: 24px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 9999; }
    #avatar-panel { position: fixed; bottom: 96px; right: 24px; width: 340px; height: 480px;
      background: white; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.15);
      display: none; flex-direction: column; z-index: 9999; overflow: hidden; }
    #avatar-panel.open { display: flex; }
    #avatar-messages { flex: 1; overflow-y: auto; padding: 16px; font-family: sans-serif; font-size: 14px; }
    .avatar-msg { margin: 8px 0; padding: 8px 12px; border-radius: 8px; max-width: 80%; }
    .avatar-msg.user { background: #4f46e5; color: white; margin-left: auto; }
    .avatar-msg.bot { background: #f3f4f6; }
    #avatar-input-row { display: flex; padding: 8px; border-top: 1px solid #e5e7eb; }
    #avatar-input { flex: 1; padding: 8px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; }
    #avatar-send { margin-left: 8px; padding: 8px 14px; background: #4f46e5; color: white;
      border: none; border-radius: 6px; cursor: pointer; }
  `
  document.head.appendChild(style)

  document.body.insertAdjacentHTML('beforeend', `
    <div id="avatar-bubble">💬</div>
    <div id="avatar-panel">
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
  let history = []

  bubble.addEventListener('click', () => panel.classList.toggle('open'))

  async function sendMessage() {
    const text = input.value.trim()
    if (!text) return
    input.value = ''

    messages.insertAdjacentHTML('beforeend', `<div class="avatar-msg user">${text}</div>`)
    history.push({ role: 'user', content: text })

    const res = await fetch(`${apiUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ embed_token: token, message: text, history })
    })
    const data = await res.json()
    messages.insertAdjacentHTML('beforeend', `<div class="avatar-msg bot">${data.response}</div>`)
    history.push({ role: 'assistant', content: data.response })
    messages.scrollTop = messages.scrollHeight
  }

  sendBtn.addEventListener('click', sendMessage)
  input.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage() })
})()