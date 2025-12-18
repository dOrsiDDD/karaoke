<template>
  <div class="youtube-container">
    <div v-if="playerReady" id="youtube-player"></div>
    <div v-else class="loading-placeholder">
      Carregando player...
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  videoId: {
    type: String,
    required: true
  }
})

const emits = defineEmits(['started', 'paused', 'ended', 'video-unplayable', 'player-ready'])

const player = ref(null)
const playerReady = ref(false)

// Carrega a API do YouTube
function loadYouTubeAPI() {
  console.log('Carregando API do YouTube...')
  playerReady.value = true
  return new Promise((resolve) => {
    if (window.YT) {
      resolve()
      return
    }

    const tag = document.createElement('script')
    tag.src = 'https://www.youtube.com/iframe_api'
    const firstScriptTag = document.getElementsByTagName('script')[0]
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag)

    window.onYouTubeIframeAPIReady = () => resolve()
  })
  
}

// Inicializa o player
function initPlayer() {
  player.value = new YT.Player('youtube-player', {
    height: '390',
    width: '640',
    videoId: props.videoId,
    playerVars: {
      autoplay: 1,
      modestbranding: 1,
      rel: 0
    },
    events: {
      onReady: (event) => {
          console.log('Evento onReady disparado');
          onReady(event);
        },
        onStateChange: (event) => {
          console.log('Estado alterado:', event.data);
          onStateChange(event);
        },
        onError: (error) => {
          console.error('Erro no player:', error.data);
        }
    }
  })
  console.log('Player inicializado com videoId:', props.videoId)
}

function onReady(event) {
  event.target.playVideo()
  console.log('Player pronto para tocar o vídeo:', props.videoId)
}

async function onError(event) {
  console.error("Erro no player do YouTube:", event.data);

  // Erros 100, 101, 150 geralmente indicam conteúdo bloqueado ou removido
  if ([100, 101, 150].includes(event.data)) {
    // 'currentSong' deve ser o objeto da música que está tentando tocar
    // Ele agora tem 'karaokeVideoId' e 'channelId' graças às nossas mudanças no backend
    const song = currentSong.value; 

    if (!song) return;

    console.log(`Vídeo ${song.karaokeVideoId} não pode ser tocado. Reportando...`);

    // 1. Reporta o vídeo para o backend
    try {
      await fetch("http://localhost:8000/report_bad_video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: song.karaokeVideoId,
          channel_id: song.channelId, // Enviando o ID do canal
          reason: `Player Error ${event.data}`
        }),
      });
      console.log("Vídeo reportado com sucesso!");
    } catch (err) {
      console.error("Falha ao reportar o vídeo:", err);
    }

    // 2. Lógica para pular para a próxima música na fila (exemplo)
    // Você precisará adaptar isso à sua lógica de gerenciamento de fila
    removeSongFromQueue(song.karaokeVideoId); // Remove a música quebrada
    playNextSong(); // Toca a próxima da fila
  }
}

function onStateChange(event) {
  switch(event.data) {
    case YT.PlayerState.PLAYING:
      emits('started')
      break
    case YT.PlayerState.PAUSED:
      emits('paused')
      break
    case YT.PlayerState.ENDED:
      emits('ended')
      break
  }
}

onMounted(async () => {
  await loadYouTubeAPI()
  initPlayer()
})

onBeforeUnmount(() => {
  if (player.value && player.value.destroy) {
    player.value.destroy()
  }
})

watch(() => props.videoId, (newVal) => {
  if (newVal && player.value && player.value.loadVideoById) {
    player.value.loadVideoById(newVal)
  }
})
</script>

<style scoped>
.youtube-container {
  width: 640px;
  height: 390px;
  position: relative;
}

.loading-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fbead1;
  color: #f15a24;
}
</style>