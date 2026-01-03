<template>
  <ul class="queue-list">
    <li v-for="song in songs" :key="song">{{ song.artist }} - {{ song.title }} <button @click="removeSong(song)">-</button></li>
  </ul>
</template>

<script setup>
import { emit } from '@tauri-apps/api/event';


const emits = defineEmits(['remove-first-song'])

const props = defineProps({
  songs: Array
})

async function removeSong(song) {
  const index = props.songs.findIndex(
    queuedSong => queuedSong.karaoke_video_id === song.karaoke_video_id
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
.queue-list {
  list-style: none;
  padding: 0;
  margin-top: 0.5rem;
}

.queue-list li {
  margin: 0.5rem 0;
  color: #8a078f;
  cursor: pointer;
}

.queue-list button {
  margin-left: 1rem;
  background-color: #000000;
  border: none;
  color: #8a078f;
  cursor: pointer;
}
</style>
