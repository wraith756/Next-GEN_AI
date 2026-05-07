import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import dynamic from 'next/dynamic'
import JarvisHUD from '../components/JarvisHUD'

const FaceAuthOverlay = dynamic(() => import('../components/FaceAuthOverlay'), { ssr: false })

type AuthStep = 'loader' | 'scanning' | 'success' | 'greet'

export default function StartPage() {
  const router = useRouter()
  const [step, setStep] = useState<AuthStep>('loader')
  const [message, setMessage] = useState('Initializing...')

  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js'
    document.head.appendChild(script)

    const t = setTimeout(() => {
      setStep('scanning')
      setMessage('Ready for Face Authentication')
      doAuth()
    }, 1500)
    return () => clearTimeout(t)
  }, [])

  async function doAuth() {
    try {
      const res = await fetch('/api/auth/face', { method: 'POST' })
      const data = await res.json()
      if (data.success) {
        setStep('success')
        setMessage('Face Authentication Successful')
        setTimeout(() => {
          setStep('greet')
          setMessage('Hello, Welcome Sir')
          setTimeout(() => router.push('/assistant'), 2000)
        }, 1500)
      } else {
        setMessage('Face Authentication Failed — Retrying...')
        setTimeout(doAuth, 2000)
      }
    } catch {
      setMessage('Authentication error — Retrying...')
      setTimeout(doAuth, 3000)
    }
  }

  return (
    <div className="container">
      <section id="Start">
        <div className="row">
          <div className="col-lg-12">
            <div className="d-flex justify-content-center align-items-center" style={{ height: '80vh' }}>
              <div>
                {step === 'loader' && <JarvisHUD />}
                {step !== 'loader' && <FaceAuthOverlay step={step} message={message} />}
              </div>
            </div>
            <div className="d-flex justify-content-center align-items-center">
              <h1 className="text-center text-light mt-4">
                {step === 'loader' ? message : ''}
              </h1>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
