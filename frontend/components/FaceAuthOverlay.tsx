import dynamic from 'next/dynamic'

const LottiePlayer = dynamic(
  () => import('@lottiefiles/lottie-player').then(() => {
    const el: any = () => null
    el.displayName = 'LottiePlayer'
    return { default: el }
  }),
  { ssr: false }
)

export type AuthStep = 'loader' | 'scanning' | 'success' | 'greet'

interface Props {
  step: AuthStep
  message: string
}

export default function FaceAuthOverlay({ step, message }: Props) {
  return (
    <div className="d-flex justify-content-center align-items-center flex-column" style={{ height: '80vh' }}>
      {step === 'scanning' && (
        <div id="FaceAuth" className="mb-4">
          {/* @ts-ignore */}
          <lottie-player
            src="https://assets2.lottiefiles.com/temp/lf20_XcJCfR.json"
            background="transparent"
            speed="1"
            style={{ width: 300, height: 300 }}
            loop
            autoplay
          />
        </div>
      )}
      {step === 'success' && (
        <div id="FaceAuthSuccess" className="mb-4">
          {/* @ts-ignore */}
          <lottie-player
            src="https://assets1.lottiefiles.com/packages/lf20_lk80fpsm.json"
            background="transparent"
            speed="1"
            style={{ width: 300, height: 300 }}
            loop
            autoplay
          />
        </div>
      )}
      {step === 'greet' && (
        <div id="HelloGreet" className="mb-4">
          {/* @ts-ignore */}
          <lottie-player
            src="https://lottie.host/f60d18d4-5199-412c-b687-e5e63ae38f75/CoqjMcJIx0.json"
            background="transparent"
            speed="1"
            style={{ width: 300, height: 300 }}
            loop
            autoplay
          />
        </div>
      )}
      <h1 className="text-center text-light mt-4">{message}</h1>
    </div>
  )
}
