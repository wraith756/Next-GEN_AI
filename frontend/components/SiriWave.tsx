import { useEffect, useRef } from 'react'

interface Props {
  visible: boolean
  message?: string
}

export default function SiriWave({ visible, message }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const waveRef = useRef<any>(null)

  useEffect(() => {
    if (!containerRef.current) return
    let SiriWaveLib: any
    try {
      SiriWaveLib = require('siriwave')
      const Ctor = SiriWaveLib.default || SiriWaveLib
      waveRef.current = new Ctor({
        container: containerRef.current,
        width: 800,
        height: 200,
        style: 'ios9',
        amplitude: 1,
        speed: 0.3,
        autostart: true,
      })
    } catch {}
    return () => { try { waveRef.current?.stop() } catch {} }
  }, [])

  if (!visible) return null

  return (
    <section id="SiriWave" className="mb-4">
      <div className="container">
        <div className="row">
          <div className="col-md-12">
            <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
              <div>
                <p className="text-start text-light mb-4 siri-message" style={{ fontSize: 28 }}>
                  {message || 'Hello, I am J.A.R.V.I.S'}
                </p>
                <div ref={containerRef} id="siri-container" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
