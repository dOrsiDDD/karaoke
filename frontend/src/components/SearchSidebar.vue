<template>
  <div class="sidebar">
    <div class="search-area">
      <div class="search-header">
        <span>Catálogo</span>
        <h2>Buscar música</h2>
        <p>{{ searchHint }}</p>
      </div>

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
        <div v-if="results.length === 0" class="search-empty">
          <div class="search-empty-icon">⌕</div>
          <strong>Nenhum resultado exibido</strong>
          <p>Digite o nome de uma música e clique em buscar.</p>
        </div>
        
        <div
          v-for="(song, idx) in results"
          v-else
          :key="idx"
          class="search-item"
        >

          <div class="search-item-info">
            <strong>{{ song.title || 'Música sem título' }}</strong>
            <span>{{ mode === 'catalog' ? 'Já cadastrada' : 'Resultado do YouTube' }}</span>
          </div>

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

const searchHint = computed(() =>
  mode.value === 'catalog'
    ? 'Encontre músicas já processadas e prontas para cantar.'
    : 'Busque um karaokê no YouTube para adicionar ao catálogo.'
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
  min-height: 0;
  gap: 0.9rem;
}

.search-area,
.queue-section {
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 1rem;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.015)),
    #250049;
  box-shadow: 0 16px 42px rgba(0, 0, 0, 0.18);
}

.search-area {
  padding: 1rem;
  color: #f8edff;
}

.search-header {
  margin-bottom: 0.9rem;
}

.search-header span {
  color: #d8b4fe;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.search-header h2 {
  margin: 0.15rem 0 0.25rem;
  color: #ffffff;
  font-size: 1.35rem;
  font-weight: 800;
}

.search-header p {
  margin: 0;
  color: rgba(248, 237, 255, 0.68);
  font-size: 0.86rem;
  line-height: 1.35;
}

.modes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.45rem;
  margin-bottom: 0.75rem;
  padding: 0.25rem;
  border-radius: 0.85rem;
  background: rgba(0, 0, 0, 0.18);
}

.modes button {
  border: none;
  border-radius: 0.65rem;
  background: transparent;
  color: #d8b4fe;
  padding: 0.6rem 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 700;
  transition:
    background 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease;
}

.modes button:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.06);
}

.modes button.active {
  background: linear-gradient(135deg, #c77dff, #f0c3ff);
  color: #250049;
}

.search-bar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.5rem;
}

.search-bar input {
  min-width: 0;
  padding: 0.72rem 0.85rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.75rem;
  outline: none;
  background: rgba(255, 255, 255, 0.96);
  color: #250049;
  font-size: 0.92rem;
}

.search-bar input::placeholder {
  color: rgba(42, 0, 77, 0.55);
}

.search-bar input:focus {
  border-color: #f0c3ff;
  box-shadow: 0 0 0 3px rgba(199, 125, 255, 0.18);
}

.search-bar button {
  min-width: 82px;
  border: none;
  border-radius: 0.75rem;
  background: linear-gradient(135deg, #c77dff, #f0c3ff);
  color: #250049;
  padding: 0.72rem 0.85rem;
  font-weight: 800;
  cursor: pointer;
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}

.search-bar button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.search-bar button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  height: 145px;
  margin-top: 0.85rem;
  overflow-y: auto;
  padding-right: 0.2rem;
}

.search-empty {
  height: 100%;
  display: grid;
  place-items: center;
  align-content: center;
  padding: 1rem;
  border: 1px dashed rgba(255, 255, 255, 0.14);
  border-radius: 0.8rem;
  color: #d8b4fe;
  text-align: center;
}

.search-empty-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  margin-bottom: 0.6rem;
  border-radius: 999px;
  background: rgba(199, 125, 255, 0.14);
  color: #f0c3ff;
  font-size: 1.25rem;
}

.search-empty strong {
  color: #ffffff;
  font-size: 0.94rem;
  font-weight: 800;
}

.search-empty p {
  max-width: 230px;
  margin: 0.3rem 0 0;
  color: rgba(248, 237, 255, 0.62);
  font-size: 0.82rem;
  line-height: 1.25;
}

.search-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.7rem;
  padding: 0.7rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.8rem;
  background: rgba(255, 255, 255, 0.055);
  color: #f3e8ff;
}

.search-item-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.search-item-info strong {
  overflow: hidden;
  color: #ffffff;
  font-size: 0.9rem;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-item-info span {
  margin-top: 0.1rem;
  color: rgba(248, 237, 255, 0.58);
  font-size: 0.76rem;
}

.search-item button {
  border: none;
  border-radius: 0.65rem;
  background: #8a078f;
  color: #fff;
  padding: 0.5rem 0.7rem;
  cursor: pointer;
  white-space: nowrap;
  font-size: 0.78rem;
  font-weight: 800;
}

.search-item button:hover {
  background: #b517b8;
}

.queue-section {
  flex: 1;
  min-height: 230px;
  overflow: auto;
  padding: 1rem;
}

.queue-section h2 {
  margin: 0 0 0.9rem;
  color: #f0c3ff;
  font-size: 1.35rem;
  font-weight: 800;
}
</style>
