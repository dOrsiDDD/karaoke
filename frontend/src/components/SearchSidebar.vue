<template>
  <div class="sidebar">
    <div class="search-area">
      <div class="modes">
        <button
          type="button"
          :class="{ active: mode === 'catalog' }"
          @click="setMode('catalog')"
        >Buscar no catálogo</button>
        <button
          type="button"
          :class="{ active: mode === 'youtube' }"
          @click="setMode('youtube')"
        >Adicionar ao catálogo</button>
      </div>

      <form class="search-bar" @submit.prevent="onSearch">
        <input v-model="query" :placeholder="placeholderText" />
        <button type="submit" :disabled="!query">Buscar</button>
      </form>

      <div class="search-results">
        <div v-for="(song, idx) in results" :key="idx" class="search-item">
          <span>{{ song.title }}</span>
          <button type="button" @click="addSong(song)">
            {{ actionLabel }}
          </button>
        </div>
      </div>
    </div>

    <div class="queue-section">
      <h2>Fila</h2>
      <SongQueue :songs="queue" @remove-first-song="emit('skip-song')" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import SongQueue from './SongQueue.vue'
import { searchKaraoke, searchCatalog } from '../composables/useKaraokeApi'

defineProps({
  queue: { type: Array, default: () => [] },
})

const emit = defineEmits(['add-song', 'skip-song'])

const query = ref('')
const results = ref([])
const mode = ref('catalog')

const placeholderText = computed(() =>
  mode.value === 'catalog'
    ? 'Buscar músicas já cadastradas'
    : 'Buscar karaoke no YouTube para adicionar'
)

const actionLabel = computed(() =>
  mode.value === 'catalog' ? 'Adicionar à fila' : 'Adicionar ao catálogo'
)

function setMode(value) {
  mode.value = value
  results.value = []
}

async function onSearch() {
  try {
    if (mode.value === 'catalog') {
      results.value = await searchCatalog(query.value)
    } else {
      results.value = await searchKaraoke(query.value)
    }
    query.value = ''
  } catch (err) {
    console.error('Erro ao buscar:', err)
    results.value = []
  }
}

function addSong(song) {
  const payload = {
    ...song,
    source: mode.value === 'catalog' ? 'catalog' : 'youtube',
    query: song.query ?? query.value,
  }
  emit('add-song', payload)
}
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.search-area {
  padding: 1rem;
  border-radius: 0.75rem;
  background: #2a004d;
  color: #000000;
  margin-bottom: 1rem;
}

.modes {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.modes button {
  flex: 1;
  border: none;
  background: #8a078f;
  color: #fff;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  cursor: pointer;
}

.modes button.active {
  background: #c77dff;
  color: #2a004d;
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
  color: #f3e8ff;
  gap: 0.5rem;
}

.search-item span {
  flex: 1;
  font-size: 0.9rem;
}

.search-item button {
  background: #8a078f;
  color: #fff;
  padding: 0.4rem 0.75rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  white-space: nowrap;
  font-size: 0.85rem;
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
