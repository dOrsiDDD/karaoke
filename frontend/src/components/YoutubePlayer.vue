<template>
  <div class="youtube-container">
    <div id="youtube-player"></div>
    <div v-if="!playerReady" class="loading-placeholder">Carregando player...</div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  videoId: { type: String, required: true },
})

const emits = defineEmits(['started', 'playing', 'paused', 'ended', 'timeupdate'])

const player = ref(null)
const playerReady = ref(false)
let timeInterval = null
let hasStarted = false

function loadYouTubeAPI() {
  return new Promise((resolve) => {
    if (window.YT) {
      resolve()
      return
    }
    const tag = document.createElement('script')
    tag.src = 'https://www.youtube.com/iframe_api'
    document.head.appendChild(tag)
    window.onYouTubeIframeAPIReady = () => resolve()
  })
}

function clearTimeInterval() {
  if (timeInterval) {
    clearInterval(timeInterval)
    timeInterval = null
  }
}

function startTimeUpdates() {
  clearTimeInterval()
  timeInterval = setInterval(() => {
    if (player.value?.getCurrentTime) {
      emits('timeupdate', player.value.getCurrentTime())
    }
  }, 50)
}

function initPlayer() {
  player.value = new YT.Player('youtube-player', {
    height: '100%',
    width: '100%',
    videoId: props.videoId,
    playerVars: { autoplay: 1, modestbranding: 1, rel: 0 },
    events: {
      onReady: (event) => {
        playerReady.value = true
        event.target.playVideo()
      },
      onStateChange: onStateChange,
      onError: (event) => console.error('Erro no player:', event.data),
    },
  })
}

function onStateChange(event) {
  switch (event.data) {
    case YT.PlayerState.PLAYING:
      startTimeUpdates()
      if (!hasStarted) {
        hasStarted = true
        emits('started')
      }
      emits('playing')
      break
    case YT.PlayerState.PAUSED:
      clearTimeInterval()
      emits('paused')
      break
    case YT.PlayerState.ENDED:
      clearTimeInterval()
      emits('ended')
      break
  }
}

onMounted(async () => {
  await loadYouTubeAPI()
  initPlayer()
})

onBeforeUnmount(() => {
  clearTimeInterval()
  player.value?.destroy?.()
})

watch(
  () => props.videoId,
  (newVal) => {
    hasStarted = false
    clearTimeInterval()
    if (newVal && player.value?.loadVideoById) {
      player.value.loadVideoById(newVal)
    }
  }
)
</script>

<style scoped>
.youtube-container {
  width: 100%;
  height: 100%;
  position: relative;
}

#youtube-player {
  width: 100%;
  height: 100%;
}

.loading-placeholder {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2a004d;
  color: #c77dff;
}
</style>
