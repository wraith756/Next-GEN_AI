import { useCallback, useState, useRef, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { useWebSocket, WSMessage } from '../hooks/useWebSocket'
import { useVoice } from '../hooks/useVoice'
import { useSession } from '../hooks/useSession'
import SessionTabs from '../components/SessionTabs'
import ChatInput from '../components/ChatInput'
import SettingsModal from '../components/SettingsModal'

const SiriWave = dynamic(() => import('../components/SiriWave'), { ssr: false })

type ChatMsg = { role: 'user' | 'assistant'; text: string; image?: string }

export default function AssistantPage() {
  const [showSiriWave, setShowSiriWave] = useState(false)
  const [displayText, setDisplayText] = useState('Ask me anything')
  const [isProcessing, setIsProcessing] = useState(false)
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const chatBottomRef = useRef<HTMLDivElement>(null)

  const { sessions, activeId, setActiveId, createSession, renameSession, deleteSession } = useSession()

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleWSMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'wake':
        setShowSiriWave(true)
        setIsProcessing(true)
        setDisplayText('Listening...')
        break
      case 'transcript':
        setDisplayText(msg.text ?? '')
        setMessages(p => [...p, { role: 'user', text: msg.text ?? '' }])
        break
      case 'display':
        setDisplayText(msg.text ?? '')
        break
      case 'response':
        setDisplayText(msg.text ?? '')
        setMessages(p => [...p, { role: 'assistant', text: msg.text ?? '' }])
        break
      case 'image':
        setMessages(p => [...p, {
          role: 'assistant',
          text: msg.text ?? 'Screenshot saved',
          image: msg.data,
        }])
        break
      case 'show_hood':
        setShowSiriWave(false)
        setIsProcessing(false)
        break
    }
  }, [])

  const { send, sendBinary } = useWebSocket(handleWSMessage)

  const handleAudio = useCallback((data: ArrayBuffer) => {
    sendBinary(data)
  }, [sendBinary])

  const { listening, startListening, stopListening } = useVoice(handleAudio)

  function handleSendText(text: string) {
    if (!activeId) return
    setIsProcessing(true)
    setShowSiriWave(true)
    setDisplayText(text)
    setMessages(p => [...p, { role: 'user', text }])
    send({ type: 'command', text, session_id: activeId })
  }

  function handleMicClick() {
    if (listening) {
      stopListening()
    } else {
      setShowSiriWave(true)
      setIsProcessing(true)
      startListening()
    }
  }

  return (
    <>
      <SessionTabs
        sessions={sessions}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={createSession}
        onRename={renameSession}
        onDelete={deleteSession}
      />

      <div className="container">
        {!showSiriWave && (
          <section id="Oval" className="mb-2">
            <div className="row">
              <div className="col-md-1" />
              <div className="col-md-10">
                {/* HUD reduced to 40vh to make room for chat panel */}
                <div className="d-flex justify-content-center align-items-center" style={{ height: '40vh' }}>
                  <div id="JarvisHood">
                    <div className="square">
                      <span className="circle" />
                      <span className="circle" />
                      <span className="circle" />
                    </div>
                  </div>
                </div>

                <h5 className="text-light text-center mb-2">{displayText}</h5>

                {/* Chat history panel */}
                <div style={{ maxHeight: '35vh', overflowY: 'auto', padding: '0 4px', marginBottom: '8px' }}>
                  {messages.map((m, i) => (
                    <div
                      key={i}
                      className={`row ${m.role === 'user' ? 'justify-content-end' : 'justify-content-start'} mb-2`}
                    >
                      <div className="width-size">
                        <div className={m.role === 'user' ? 'sender_message' : 'receiver_message'}>
                          {m.image && (
                            <a
                              href={`data:image/jpeg;base64,${m.image}`}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <img
                                src={`data:image/jpeg;base64,${m.image}`}
                                style={{ maxWidth: 200, display: 'block', marginBottom: 6, borderRadius: 4 }}
                                alt="screenshot"
                              />
                            </a>
                          )}
                          {m.text}
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={chatBottomRef} />
                </div>

                <ChatInput
                  onSendText={handleSendText}
                  onMicClick={handleMicClick}
                  isListening={listening}
                  isProcessing={isProcessing}
                />
              </div>
              <div className="col-md-1" />
            </div>
          </section>
        )}

        <SiriWave visible={showSiriWave} message={displayText} />
      </div>

      <SettingsModal />
    </>
  )
}
