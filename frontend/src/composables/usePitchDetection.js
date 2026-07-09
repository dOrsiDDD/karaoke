import { ref } from 'vue'
import { PitchDetector } from 'pitchy'
import { freqToMidi } from '../utils/noteUtils'

export function usePitchDetection() {
  const userMidi = ref(null)
  const isVoiced = ref(false)

  let audioContext = null
  let analyser = null
  let source = null
  let detector = null
  let inputBuffer = null
  let rafId = null

  let smoothedMidi = null

  const MIN_CLARITY = 0.88
  const SMOOTHING = 0.08

  function tick() {
    if (!analyser || !audioContext || !detector) return

    analyser.getFloatTimeDomainData(inputBuffer)

    const [pitch, clarity] =
      detector.findPitch(
        inputBuffer,
        audioContext.sampleRate
      )

    if (
      pitch > 0 &&
      clarity > MIN_CLARITY
    ) {
      const midi = freqToMidi(pitch)

      if (smoothedMidi === null) {
        smoothedMidi = midi
      } else {
        if (Math.abs(midi - smoothedMidi) > 5) {
          // Amortecimento ainda mais pesado para saltos bruscos
          smoothedMidi = 0.02 * midi + (1 - 0.02) * smoothedMidi
        } else {
          smoothedMidi = SMOOTHING * midi + (1 - SMOOTHING) * smoothedMidi
        }
      }

      userMidi.value = smoothedMidi
      isVoiced.value = true
    } else {
      isVoiced.value = false
      // mantém a última posição
    }

    rafId = requestAnimationFrame(tick)
  }

  async function start(stream) {
    stop()

    audioContext = new AudioContext()

    analyser = audioContext.createAnalyser()

    analyser.fftSize = 2048

    source =
      audioContext.createMediaStreamSource(
        stream
      )

    source.connect(analyser)

    inputBuffer =
      new Float32Array(analyser.fftSize)

    detector =
      PitchDetector.forFloat32Array(
        analyser.fftSize
      )

    tick()
  }

  function stop() {
    if (rafId)
      cancelAnimationFrame(rafId)

    rafId = null

    source?.disconnect()

    source = null
    analyser = null
    detector = null
    inputBuffer = null

    smoothedMidi = null

    if (audioContext) {
      audioContext.close()
      audioContext = null
    }

    userMidi.value = null
    isVoiced.value = false
  }

  return {
    userMidi,
    isVoiced,
    start,
    stop,
  }
}