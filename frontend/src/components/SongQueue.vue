<template>
  <div class="queue">
    <div v-if="!songs || songs.length === 0" class="queue-empty">
      <div class="queue-empty-icon">♪</div>
      <strong>Fila vazia</strong>
      <p>Busque uma música e adicione para começar.</p>
    </div>

    <ul v-else class="queue-list">
      <li
        v-for="(song, index) in songs"
        :key="song.karaokeVideoId || song.title || index"
        class="queue-item"
        :class="{ current: index === 0 }"
      >
        <div class="queue-index">
          {{ index === 0 ? '▶' : index + 1 }}
        </div>

        <div class="queue-content">
          <span class="queue-label">
            {{ index === 0 ? 'Tocando agora' : 'Próxima música' }}
          </span>

          <strong class="queue-title">
            {{ song.title || song.query || 'Música sem título' }}
          </strong>

          <span v-if="song.query && song.query !== song.title" class="queue-subtitle">
            Busca: {{ song.query }}
          </span>
        </div>

        <button
          type="button"
          class="queue-remove"
          :title="index === 0 ? 'Pular música' : 'Remover da fila'"
          @click="removeSong(song)"
        >
          ×
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
const emits = defineEmits(['remove-first-song'])

const props = defineProps({
  songs: Array
})

async function removeSong(song) {
  const index = props.songs.findIndex(
    queuedSong => queuedSong.karaokeVideoId === song.karaokeVideoId
  )

  if (index === 0) {
    emits('remove-first-song');
    return;
  }

  if (index > 0 && index < props.songs.length) {
    props.songs.splice(index, 1);
  }
}
</script>

<style scoped>
.queue {
  width: 100%;
}

.queue-empty {
  min-height: 140px;
  padding: 1.25rem;
  border: 1px dashed rgba(255, 255, 255, 0.18);
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.04);
  color: #f3e8ff;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.queue-empty-icon {
  width: 42px;
  height: 42px;
  margin-bottom: 0.75rem;
  border-radius: 999px;
  background: rgba(199, 125, 255, 0.16);
  color: #f0c3ff;
  display: grid;
  place-items: center;
  font-size: 1.35rem;
}

.queue-empty strong {
  font-size: 1rem;
  color: #ffffff;
}

.queue-empty p {
  max-width: 220px;
  margin: 0.35rem 0 0;
  color: #d8b4fe;
  font-size: 0.85rem;
}

.queue-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.queue-item {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) 32px;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.065);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #f3e8ff;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease;
}

.queue-item:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.095);
  border-color: rgba(240, 195, 255, 0.32);
}

.queue-item.current {
  background:
    linear-gradient(135deg, rgba(199, 125, 255, 0.24), rgba(138, 7, 143, 0.18)),
    rgba(255, 255, 255, 0.08);
  border-color: rgba(240, 195, 255, 0.42);
  box-shadow: 0 0 24px rgba(199, 125, 255, 0.18);
}

.queue-index {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.24);
  color: #f0c3ff;
  display: grid;
  place-items: center;
  font-size: 0.82rem;
  font-weight: 800;
}

.queue-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.queue-label {
  margin-bottom: 0.15rem;
  color: #d8b4fe;
  font-size: 0.67rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.queue-title {
  overflow: hidden;
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.queue-subtitle {
  overflow: hidden;
  margin-top: 0.1rem;
  color: rgba(243, 232, 255, 0.62);
  font-size: 0.78rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.queue-remove {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.24);
  color: #f0c3ff;
  cursor: pointer;
  font-size: 1.15rem;
  line-height: 1;
  transition:
    background 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease;
}

.queue-remove:hover {
  background: #ff4d8d;
  color: #ffffff;
  transform: scale(1.06);
}
</style>