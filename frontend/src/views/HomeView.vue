<template>
  <div class="main-container">
    <header>
      <h1>Krlhoke</h1>
      <div class="menu-icon">☰</div>
    </header>

    <div class="content">
      <ResultsOverlay
          v-if="showResultsOverlay"
          :score="score"
          :loading="isScoring"
          @close="closeResults"
        />
      <div class="layout">
        <div class="player-section">
          <div class="player-wrapper">
              <YoutubePlayer
                v-if="currentVideoId"
                :videoId="currentVideoId"
                @started="startRecording"
                @paused="pauseRecording"
                @playing="resumeRecording"
                @ended="handleEnded"
              />
            <div v-else class="player-placeholder">
              Selecione uma música para começar
            </div>
          </div>
        </div>
        
        <div class="sidebar">
          <div class="search-area">
            <form class="search-bar" @submit.prevent="searchSongs">
              <input v-model="searchQuery" placeholder="Buscar" />
              <button type="submit" :disabled="!searchQuery">Buscar</button>
            </form>

            <div class="search-results">
              <div v-for="(song, idx) in searchResults" :key="idx" class="search-item">
                <span>{{ song.artist }} {{ song.title }}</span>
                <button @click="addSongToQueue(song)">Adicionar à fila</button>
              </div>
            </div>
          </div>

          <div class="divider"></div>

          <div class="queue-section">
            <h2>Fila</h2>
            <SongQueue 
              :songs="upNext" 
              @remove-first-song="handleEnded" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { invoke } from '@tauri-apps/api/core';
import { appDataDir } from '@tauri-apps/api/path';

import { ref } from 'vue'
import YoutubePlayer from '../components/YoutubePlayer.vue'
import SongQueue from '../components/SongQueue.vue'
import ResultsOverlay from '../components/ResultsOverlay.vue'
import { show } from '@tauri-apps/api/app';

const currentVideoId = ref(null)
const upNext = ref([]) // lista de músicas que serão tocadas
const searchQuery = ref('')
const searchResults = ref([])
const mediaRecorder = ref(null)
const audioChunks = ref([])
const showResultsOverlay = ref(false)
const isScoring = ref(false)
const score = ref(null)

async function searchSongs() {
  try{
    const res = await fetch(`http://localhost:8000/karaoke_search?q=${encodeURIComponent(searchQuery.value)}`)
    const data = await res.json();
    console.log("Resultados da busca:", data);
    if (!res.ok) {
      searchResults.value = []
      console.log("Erro ao buscar musicas", data.detail);
    }

    searchResults.value = data.results.results ?? [];
  } catch(err) {
    console.error("Erro de rede:", err);
    searchResults.value = [];
  }
}

async function addSongToQueue(song) {

  console.log("Iniciando processo para adicionar:", song.artist, song.title);
  
  // Construir a query para buscar o vídeo original
  const originalVideoQuery = encodeURIComponent(`${song.artist} ${song.title}`);

  let originalVideoId = null;

  try {
    // Chamar endpoint para obter o ID do vídeo original
    console.log("Buscando vídeo original...");
    const res = await fetch(`http://localhost:8000/original_search?q=${originalVideoQuery}`);
    if (!res.ok) {
      throw new Error("Falha ao buscar o vídeo original no backend.");
    }
    const data = await res.json();
    originalVideoId = data.originalVideoId;

    if (originalVideoId) {
      console.log("Vídeo original encontrado:", originalVideoId);
    } else {
      console.warn("Nenhum vídeo original encontrado.");
    }

  } catch (err) {
    console.error("Erro ao buscar o ID do vídeo original:", err);
  }

  const formatted = {
    title: song.title,
    artist: song.artist,
    karaoke_video_id: song.karaokeVideoId,
    original_video_id: song.originalVideoId,
    query: song.query,
  };



  const alreadyInQueue = upNext.value.some(
    queuedSong => queuedSong.karaoke_video_id === formatted.karaoke_video_id
  );

  if (alreadyInQueue) {
    console.log("Música já está na fila");
    return;
  }

  upNext.value.push(formatted);
  if (!currentVideoId.value) currentVideoId.value = formatted.karaoke_video_id;

  try {
    if (originalVideoId) {
      const res = await fetch("http://localhost:8000/add_song", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          karaoke_url: `https://www.youtube.com/watch?v=${song.karaokeVideoId}`,
          original_url: `https://www.youtube.com/watch?v=${originalVideoId}`,
        }),
      });
    }

  
    if (!res.ok) {
      const error = await res.text();
      console.error("Erro no backend ao adicionar música:", error);
    } else {
      console.log("Música processada e salva com sucesso");
    }
  } catch (err) {
    console.error("Erro de rede ao adicionar música:", err);
  }

  searchQuery.value = ""
  searchResults.value = []
}

async function startRecording() {
 try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // Define tipo de gravação preferido
    let mimeType = "audio/webm";
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = "audio/ogg";
    }

    mediaRecorder.value = new MediaRecorder(stream, { mimeType });
    audioChunks.value = [];

    mediaRecorder.value.ondataavailable = (event) => {
      console.log("Chunk de áudio recebido:", event.data.size)
      if (event.data.size > 0) {
        audioChunks.value.push(event.data);
      }
    };

    mediaRecorder.onstart = () => console.log("Gravação iniciada")
    mediaRecorder.onstop = () => console.log("Gravação parada, total de chunks:", audioChunks.length)

    mediaRecorder.value.onstop = () => {
      console.log("Gravação finalizada:", blob);
    };

    mediaRecorder.value.start();
    console.log("Gravação iniciada com tipo:", mimeType);
  } catch (err) {
    console.error("Erro ao iniciar gravação:", err);
  }
}


function pauseRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.pause()
    console.log("Gravação pausada")
  }
}

function resumeRecording() {
  if (mediaRecorder && mediaRecorder.state === 'paused') {
    mediaRecorder.resume()
    console.log("Gravação retomada")
  }
}


async function stopRecording() {
   return new Promise((resolve) => {
    if (mediaRecorder.value && mediaRecorder.value.state !== "inactive") {
      mediaRecorder.value.onstop = () => {
        const mimeType = mediaRecorder.value.mimeType || "audio/webm"
        const blob = new Blob(audioChunks.value, { type: mimeType })
        console.log("Gravação finalizada:", blob)
        resolve(blob)
      }
      mediaRecorder.value.stop()
    } else {
      resolve(null)
    }
  })
}

async function analyzeRecording(blob) {
  if (!blob) {
    console.error("Nenhum áudio gravado para analisar") 
    return
  }

  isScoring.value = true
  showResultsOverlay.value = true
  score.value = null

  const formData = new FormData()
  formData.append("karaoke_video_id", currentVideoId.value)
  formData.append("user_audio", blob)

  try {
    const res = await fetch("http://localhost:8000/analyze", {
      method: "POST",
      body: formData
    })

    const data = await res.json()
    console.log("Resposta da análise:", data.score)

    score.value = data.score
  } catch (err) {
    console.error("Erro ao analisar gravação:", err)
    score.value = 0
  } finally {
    isScoring.value = false
  }
}



async function handleEnded() {
  const blob = await stopRecording()

  if (blob) {
    await analyzeRecording(blob)
  } else {
    console.warn("Nenhum blob retornado")
  }

  audioChunks.value = []
  mediaRecorder.value = null
}

function closeResults() {
  showResultsOverlay.value = false
  score.value = null

  upNext.value.shift() // remove a música atual da fila
  currentVideoId.value = upNext.value.length > 0 ? upNext.value[0].karaoke_video_id : null // toca a próxima música ou fica nulo
}
</script>

<style scoped>
.main-container {
  background: linear-gradient(180deg, #5b01afd8, #3a0073);
  padding: 1rem;
  font-family: sans-serif;
  color: #f3e8ff;
  min-height: 100vh;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 50px;
}

header h1 {
  color: #f0c3ff;
  margin: 0;
}

.menu-icon {
  font-size: 1.5rem;
  color: #8a078f;
  cursor: pointer;
}

.layout {
  display: grid;
  grid-template-columns: 3fr 1.2fr;
  gap: 1rem;
  height: calc(100vh - 100px);
}

.player-section {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.player-wrapper {
  flex: 1;
  background: #2a004d;
  border-radius: 0.75rem;
  overflow: hidden;
}

.player-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c77dff;
  font-size: 1.5rem;
}

.side-bar {
  display: flex;
  flex-direction: column;
  background: #c77dff;
  gap: 1rem;
  height: 100%;
}

.search-area {
  padding: 1rem;
  border-radius: 0.75rem;
  background: #2a004d;
  color: #000000;
  margin-bottom: 1rem;
}

.search-bar {
  display: flex;
  gap: 0.5rem;
}

.search-bar input {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 0.5rem;
}

.search-bar button {
  background: #c77dff;
  color: #2a004d;
  border: none;
  border-radius: 0.5rem;
  font-weight: bold;
  cursor: pointer;
}

.search-results {
  min-height: 160px;
  border-radius: 0.5rem;
  padding: 0.5rem;
}

.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
  border-radius: 0.4rem;
  padding: 0.5rem;
}

.search-item button {
  background: #8a078f;
  color: rgb(0, 0, 0);
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.queue-section h2 {
  margin-top: 0;
  color: #f0c3ff;
}

.queue-section {
  padding: 1rem;
  border-radius: 0.75rem;
  flex: 1;
  background: #2a004d;
}

</style>
