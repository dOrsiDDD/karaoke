<template>
  <div class="main-container">
    <header>
      <h1>Diegoke</h1>
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

          <PitchFeedbackBar
            v-if="currentVideoId"
            :segments="segments"
            :current-time="currentTime"
            :user-midi="userMidi"
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
import { ref } from 'vue'
import YoutubePlayer from '../components/YoutubePlayer.vue'
import SearchSidebar from '../components/SearchSidebar.vue'
import ResultsOverlay from '../components/ResultsOverlay.vue'
import PitchFeedbackBar from '../components/PitchFeedbackBar.vue'
import { useAudioRecording } from '../composables/useAudioRecording'
import { useSongQueue } from '../composables/useSongQueue'
import { analyzeRecording } from '../composables/useKaraokeApi'

const { userMidi, start, pause, resume, stop, reset } = useAudioRecording()
const { currentVideoId, upNext, segments, addSong, advanceQueue } = useSongQueue()

const currentTime = ref(0)
const showResultsOverlay = ref(false)
const isScoring = ref(false)
const score = ref(null)

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
  min-height: 0;
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
</style>
