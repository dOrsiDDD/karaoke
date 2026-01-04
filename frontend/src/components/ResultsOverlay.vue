<template>
  <div class="overlay">
    <div class="card">
      
      <!-- LOADING -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Analisando sua performance...</p>
      </div>

      <!-- RESULTADO -->
      <div v-else class="result">
        <div class="score">
          {{ score }}/100
        </div>

        <div class="stars">
          <span
            v-for="i in 5"
            :key="i"
            class="star"
            :class="{ filled: i <= starCount }"
          >
            ★
          </span>
        </div>

        <button @click="$emit('close')">
          Continuar
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed, watch, onBeforeUnmount } from "vue"

const props = defineProps({
  score: Number,
  loading: Boolean,
  autoCloseAfter: {
    type: Number,
    default: 5000
  }
})

const emits = defineEmits(['close'])

const starCount = computed(() => {
  if (props.score == null) return 0
  if (props.score >= 90) return 5
  if (props.score >= 75) return 4
  if (props.score >= 60) return 3
  if (props.score >= 40) return 2
  return 1
})

let timeoutId = null

watch(
  () => props.score,
  (newScore) => {
    if (newScore !== null) {
      timeoutId = setTimeout(() => {
        emits("close")
      }, props.autoCloseAfter)
    }
  }
)

onBeforeUnmount(() => {
  if (timeoutId) clearTimeout(timeoutId)
})
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0 }
  to { opacity: 1 }
}

.card {
  width: 85vw;
  height: 85vh;
  max-width: 1100px;
  max-height: 700px;
  background: #121212;
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.loading p {
  margin-top: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #333;
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.score {
  font-size: 64px;
  font-weight: bold;
  margin: 16px 0;
}

.stars {
  margin-bottom: 24px;
}

.star {
  font-size: 28px;
  color: gold;
}
.star.filled {
  color: gold;
}
.star:not(.filled) {
  color: #555;
}
</style>