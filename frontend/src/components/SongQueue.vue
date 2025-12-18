<template>
  <ul class="queue-list">
    <li v-for="song in songs" :key="song">{{ song.artist }} - {{ song.title }}</li>
  </ul>
</template>

<script setup>
const props = defineProps({
  songs: Array
})
</script>

<style scoped>
.queue-list {
  list-style: none;
  padding: 0;
  margin-top: 0.5rem;
}

.queue-list li {
  margin: 0.5rem 0;
  color: #f15a24;
  cursor: pointer;
}
</style>
