import { useState } from 'react'

interface Props {
  onSendText: (text: string) => void
  onMicClick: () => void
  isListening: boolean
  isProcessing: boolean
}

export default function ChatInput({ onSendText, onMicClick, isListening, isProcessing }: Props) {
  const [value, setValue] = useState('')

  function handleSend() {
    const text = value.trim()
    if (text && !isProcessing) {
      onSendText(text)
      setValue('')
    }
  }

  function handleKeyPress(e: React.KeyboardEvent) {
    if (e.key === 'Enter') { e.preventDefault(); handleSend() }
  }

  return (
    <div className="col-md-12 mt-4 pt-4">
      <div className="text-center">
        <div id="TextInput" className="d-flex">
          <input
            type="text"
            className="input-field"
            placeholder="type here ..."
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isProcessing}
          />
          {value.trim() ? (
            <button id="SendBtn" className="glow-on-hover" onClick={handleSend} disabled={isProcessing}>
              <i className="bi bi-send" />
            </button>
          ) : (
            <button
              id="MicBtn"
              className="glow-on-hover"
              onClick={onMicClick}
              disabled={isProcessing}
              style={isListening ? { background: '#002bff' } : {}}
            >
              <i className={`bi ${isListening ? 'bi-mic-fill' : 'bi-mic'}`} />
            </button>
          )}
          <button
            id="SettingsBtn"
            className="glow-on-hover"
            data-bs-toggle="modal"
            data-bs-target="#settingsModal"
          >
            <i className="bi bi-gear" />
          </button>
        </div>
      </div>
    </div>
  )
}
