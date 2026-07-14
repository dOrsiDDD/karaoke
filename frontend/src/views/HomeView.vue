<template>
  <div class="main-container">
    <header>
      <h1>Karaoke</h1>
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
              @started="start"
              @paused="pause"
              @playing="resume"
              @ended="handleEnded"
              @timeupdate="currentTime = $event"
            />
            <div v-else class="player-placeholder">
              Selecione uma música para começar
            </div>
          </div>

          <div class="sync-toggle" v-if="currentSong">
            <label>
              <input type="checkbox" v-model="showSyncControls" />
              Ajustar sincronia
            </label>
          </div>

          <div class="sync-panel" v-if="currentSong && showSyncControls">
            <h2>Ajuste de Sincronia</h2>
            <div class="sync-controls">
              <input
                type="range"
                min="-10"
                max="10"
                step="0.1"
                v-model.number="syncOffset"
              />
              <span>{{ syncOffset.toFixed(1) }}s</span>
            </div>
            <button :disabled="savingSync" @click="saveSyncOffset">
              {{ savingSync ? 'Salvando...' : syncMessage || 'Salvar Sincronia' }}
            </button>
          </div>

          <PitchFeedbackBar
            v-if="currentVideoId"
            :segments="segments"
            :current-time="currentTime"
            :user-midi="userMidi"
            :sync-offset="syncOffset"
          />
        </div>

        <SearchSidebar
          :queue="upNext"
          @add-song="onAddSong"
          @skip-song="skipSong"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import YoutubePlayer from '../components/YoutubePlayer.vue'
import SearchSidebar from '../components/SearchSidebar.vue'
import ResultsOverlay from '../components/ResultsOverlay.vue'
import PitchFeedbackBar from '../components/PitchFeedbackBar.vue'
import { useAudioRecording } from '../composables/useAudioRecording'
import { useSongQueue } from '../composables/useSongQueue'
import { analyzeRecording, saveSongSyncOffset } from '../composables/useKaraokeApi'

const { userMidi, start, pause, resume, stop, reset } = useAudioRecording()
const { currentVideoId, currentSong, upNext, segments, addSong, advanceQueue } = useSongQueue()

const currentTime = ref(0)
const showResultsOverlay = ref(false)
const isScoring = ref(false)
const score = ref(null)
const showSyncControls = ref(false)
const syncOffset = ref(0)
const savingSync = ref(false)
const syncMessage = ref('')

async function onAddSong(song) {
  await addSong(song)
}

async function handleEnded() {
  const blob = await stop()
  if (blob) await runAnalysis(blob)
  reset()
  currentTime.value = 0
}

async function skipSong() {
  await stop()
  reset()
  currentTime.value = 0
  await advanceQueue()
}

async function closeResults() {
  showResultsOverlay.value = false
  score.value = null
  currentTime.value = 0
  await advanceQueue()
}

async function saveSyncOffset() {
  if (!currentVideoId.value) return
  savingSync.value = true
  syncMessage.value = ''

  try {
    await saveSongSyncOffset(currentVideoId.value, syncOffset.value)
    syncMessage.value = 'Salvo!'
    setTimeout(() => {
      if (syncMessage.value === 'Salvo!') syncMessage.value = ''
    }, 2000)
  } catch (err) {
    console.error('Erro ao salvar sincronia:', err)
    syncMessage.value = 'Erro ao salvar'
  } finally {
    savingSync.value = false
  }
}

watch(currentSong, (song) => {
  syncOffset.value = Number(song?.syncOffset ?? 0)
  showSyncControls.value = false
})

async function runAnalysis(blob) {
  isScoring.value = true
  showResultsOverlay.value = true
  score.value = null

  try {
    score.value = await analyzeRecording(currentVideoId.value, blob)
  } catch (err) {
    console.error('Erro ao analisar gravação:', err)
    score.value = 0
  } finally {
    isScoring.value = false
  }
}
</script>

<style scoped>
.main-container {
  background:
    radial-gradient(circle at top left, rgba(199, 125, 255, 0.24), transparent 34%),
    linear-gradient(180deg, #4b008f, #260047);
  padding: 0.75rem 1rem 1rem;
  font-family: Inter, system-ui, sans-serif;
  color: #f3e8ff;
  min-height: 100vh;
  overflow: hidden;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 44px;
  margin-bottom: 0.75rem;
}

header h1 {
  color: #f0c3ff;
  margin: 0;
  font-size: clamp(1.7rem, 2vw, 2.4rem);
  font-weight: 800;
  letter-spacing: 0.02em;
}

.menu-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  font-size: 1.35rem;
  color: #d8b4fe;
  cursor: pointer;
  transition:
    background 0.18s ease,
    transform 0.18s ease;
}

.menu-icon:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-1px);
}

.content {
  height: calc(100vh - 60px);
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 3.9fr) minmax(320px, 1fr);
  gap: 0.9rem;
  height: 100%;
}

.player-section {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 0.65rem;
}

.player-wrapper {
  flex: 1;
  min-height: 0;
  background: #09000f;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
}

.player-placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  padding: 2rem;
  color: #d8b4fe;
  font-size: clamp(1.2rem, 1.6vw, 1.8rem);
  font-weight: 500;
  letter-spacing: 0.03em;
  text-align: center;
}

@media (max-width: 980px) {
  .main-container {
    overflow: auto;
  }

  .content {
    height: auto;
  }

  .layout {
    grid-template-columns: 1fr;
    height: auto;
  }

  .player-wrapper {
    min-height: 420px;
  }
}

.sync-panel {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.75rem;
  max-width: 420px;
}

.sync-panel h2 {
  margin: 0 0 0.75rem;
  font-size: 1rem;
  color: #c7f1ff;
}

.sync-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.sync-controls input[type='range'] {
  flex: 1;
}

.sync-panel button {
  background: #00c6ff;
  color: #08101d;
  border: none;
  border-radius: 999px;
  padding: 0.5rem 0.9rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.sync-panel button:disabled {
  background: #6c7a89;
  cursor: not-allowed;
}
</style>
