import { useCallback, useState } from 'react'
import dynamic from 'next/dynamic'
import { useWebSocket, WSMessage } from '../hooks/useWebSocket'
import { useVoice } from '../hooks/useVoice'
import { useSession } from '../hooks/useSession'
import SessionTabs from '../components/SessionTabs'
import ChatInput from '../components/ChatInput'
import SettingsModal from '../components/SettingsModal'

const SiriWave = dynamic(() => import('../components/SiriWave'), { ssr: false })

export default function AssistantPage() {
  const [showSiriWave, setShowSiriWave] = useState(false)
  const [displayText, setDisplayText] = useState('Ask me anything')
  const [isProcessing, setIsProcessing] = useState(false)

  const { sessions, activeId, setActiveId, createSession, renameSession, deleteSession } = useSession()

  const handleWSMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'wake':
        setShowSiriWave(true)
        setIsProcessing(true)
        setDisplayText('Listening...')
        break
      case 'transcript':
        setDisplayText(msg.text ?? '')
        break
      case 'display':
        setDisplayText(msg.text ?? '')
        break
      case 'response':
        setDisplayText(msg.text ?? '')
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
          <section id="Oval" className="mb-4">
            <div className="row">
              <div className="col-md-1" />
              <div className="col-md-10">
                <div className="d-flex justify-content-center align-items-center" style={{ height: '80vh' }}>
                  <div id="JarvisHood">
                    <div className="square">
                      <span className="circle" />
                      <span className="circle" />
                      <span className="circle" />
                    </div>
                  </div>
                </div>
                <h5 className="text-light text-center">{displayText}</h5>
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
