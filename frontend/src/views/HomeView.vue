<template>
  <div class="main-container">
    <header>
      <h1>Krlhoke</h1>
      <div class="menu-icon">☰</div>
    </header>

    <div class="content">
      <div class="player-and-queue">
        <div class="player-section">
          <div class="player-wrapper">
            <div v-if="currentVideoId">
              <YoutubePlayer
                :videoId="currentVideoId"
                @started="startRecording"
                @paused="pauseRecording"
                @playing="resumeRecording"
                @ended="handleEnded"
              />
            </div>
            <div v-else class="player-placeholder">
              Selecione uma música para começar
            </div>
          </div>
          
          <form class="search-bar" @submit.prevent="searchSongs">
            <input v-model="searchQuery" placeholder="Buscar" />
            <button type="submit" :disabled="!searchQuery">Buscar</button>
          </form>

          <div v-if="searchResults && searchResults.length > 0" class="search-results">
            <div v-for="(song, idx) in searchResults" :key="idx" class="search-item">
              <span>{{ song.artist }} {{ song.title }}</span>
              <button @click="addSongToQueue(song)">Adicionar à fila</button>
            </div>
          </div>
        </div>
        
        <div class="queue-section">
          <h2>Fila</h2>
          <SongQueue 
            :songs="upNext" 
            @remove-first-song="handleEnded" />
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

const currentVideoId = ref(null)
const upNext = ref([]) // lista de músicas que serão tocadas
const searchQuery = ref('')
const searchResults = ref([])
const mediaRecorder = ref(null)
const audioChunks = ref([])

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
  const formData = new FormData()
  formData.append("karaoke_video_id", currentVideoId.value)
  formData.append("user_audio", blob)

  const res = await fetch("http://localhost:8000/analyze", {
    method: "POST",
    body: formData
  })

  const data = await res.json()
  console.log("Resposta da análise:", data.score)
  alert(`Nota : ${data.score}`)
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
  upNext.value.shift() // remove a música atual da fila
  currentVideoId.value = upNext.value.length > 0 ? upNext.value[0].karaoke_video_id : null
}
</script>

<style scoped>
.main-container {
  background: #5b01afd8;
  padding: 1rem;
  font-family: sans-serif;
  color: #370080;
  min-height: 100vh;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

header h1 {
  color: #8a078f;
  margin: 0;
}

.menu-icon {
  font-size: 1.5rem;
  color: #8a078f;
  cursor: pointer;
}

.content {
  display: flex;
  flex-direction: column;
}

.player-and-queue {
  display: flex;
  gap: 2rem;
}

.player-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.queue-section {
  width: 300px;
  background: #370080;
  padding: 1rem;
  border-radius: 0.5rem;
}

.player-wrapper {
  width: 640px;
  height: 390px;
  background: #370080;
  border-radius: 0.75rem;
  overflow: hidden;
  margin-bottom: 1rem;
}

.player-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #b724f1;
  font-size: 1.5rem;
  text-align: center;
}

.search-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  width: 640px;
}

.search-bar input {
  flex: 1;
  padding: 0.5rem;
  border: 2px solid #000000;
  border-radius: 0.5rem;
  font-size: 1rem;
}

.search-bar button {
  background: #8a078f;
  color: #000000;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: bold;
  cursor: pointer;
}

.search-results {
  list-style: none;
  padding: 0;
  margin: 0;
  width: 640px;
}

.search-results li {
  padding: 0.75rem;
  border-bottom: 1px solid #370080;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-results li button {
  background: #8a078f;
  color: rgb(0, 0, 0);
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.9rem;
  cursor: pointer;
}

.search-item {
  padding: 0.75rem;
  border-bottom: 1px solid #8a078f;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #8a078f;
  margin-bottom: 0.5rem;
  border-radius: 0.25rem;
}

.search-item button {
  background: #8a078f;
  color: rgb(0, 0, 0);
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}
</style>
