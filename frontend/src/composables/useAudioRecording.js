import { ref } from 'vue'
import { usePitchDetection } from './usePitchDetection'

export function useAudioRecording() {
  const mediaRecorder = ref(null)
  const audioChunks = ref([])
  const micStream = ref(null)
  const isRecording = ref(false)
  const { userMidi, start: startPitch, stop: stopPitch } = usePitchDetection()

  async function start() {
    if (isRecording.value) return

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      micStream.value = stream

      let mimeType = 'audio/webm'
      if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'audio/ogg'

      mediaRecorder.value = new MediaRecorder(stream, { mimeType })
      audioChunks.value = []

      mediaRecorder.value.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunks.value.push(event.data)
      }

      mediaRecorder.value.start()
      startPitch(stream)
      isRecording.value = true
    } catch (err) {
      console.error('Erro ao iniciar gravação:', err)
    }
  }

  function pause() {
    if (mediaRecorder.value?.state === 'recording') {
      mediaRecorder.value.pause()
    }
  }

  function resume() {
    if (mediaRecorder.value?.state === 'paused') {
      mediaRecorder.value.resume()
    }
  }

  function stop() {
    return new Promise((resolve) => {
      stopPitch()

      if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
        mediaRecorder.value.onstop = () => {
          const mimeType = mediaRecorder.value.mimeType || 'audio/webm'
          const blob = new Blob(audioChunks.value, { type: mimeType })
          resolve(blob.size > 0 ? blob : null)
        }
        mediaRecorder.value.stop()
      } else {
        resolve(null)
      }

      micStream.value?.getTracks().forEach((t) => t.stop())
      micStream.value = null
      isRecording.value = false
    })
  }

  function reset() {
    audioChunks.value = []
    mediaRecorder.value = null
    isRecording.value = false
  }

  return {
    userMidi,
    isRecording,
    start,
    pause,
    resume,
    stop,
    reset,
  }
}
