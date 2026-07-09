<template>
  <div class="pitch-bar" v-if="segments.length">
    <div ref="viewportRef" class="pitch-viewport">
      
      <div class="playhead-line" :style="{ left: `${centerX}px` }" />

      <div
        v-for="(seg, i) in visibleSegments"
        :key="i"
        class="note-line"
        :style="segmentStyle(seg)"
      />

      <div
        class="user-ball"
        :class="{ silent: !isVoiced || userMidi == null }"
        :style="userBallStyle"
      />
    </div>
  </div>
  <div v-else class="pitch-bar pitch-bar-empty">
    <span>Carregando melodia...</span>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  segments: { type: Array, default: () => [] },
  currentTime: { type: Number, default: 0 },
  userMidi: { type: Number, default: null },
  isVoiced: { type: Boolean, default: false },
})

const WINDOW_SEC = 6 // Quantos segundos de música aparecem na tela
const viewportRef = ref(null)
const viewportWidth = ref(600)

const pxPerSec = computed(() => viewportWidth.value / WINDOW_SEC)
const centerX = computed(() => viewportWidth.value / 2)

// --- LIMITES DINÂMICOS DA MÚSICA ---
// Encontra a nota mais baixa da música e dá uma margem de 3 semitons para o fundo
const MIN_MIDI = computed(() => {
  if (!props.segments.length) return 50
  return Math.min(...props.segments.map(s => s.note)) - 3
})

// Encontra a nota mais alta da música e dá uma margem de 3 semitons para o topo
const MAX_MIDI = computed(() => {
  if (!props.segments.length) return 80
  return Math.max(...props.segments.map(s => s.note)) + 3
})

const midiRange = computed(() => {
  const range = MAX_MIDI.value - MIN_MIDI.value
  return range <= 0 ? 1 : range
})

// Converte qualquer valor MIDI (inteiro ou decimal de crescendo) em posição Y (0% a 100%)
function midiToY(midi) {
  if (midi == null) return 50 // Centraliza por padrão caso nulo
  // Clampeia para o valor não sair voando para fora da caixa do componente
  const clamped = Math.max(MIN_MIDI.value, Math.min(MAX_MIDI.value, midi))
  // Inverte o cálculo porque no CSS, Top: 0% é o topo e 100% é o fundo
  return ((MAX_MIDI.value - clamped) / midiRange.value) * 100
}

// Filtra apenas os segmentos de nota que devem aparecer na janela de tempo atual
const visibleSegments = computed(() => {
  const half = WINDOW_SEC / 2
  const t0 = props.currentTime - half
  const t1 = props.currentTime + half
  return props.segments.filter((s) => s.end > t0 && s.start < t1)
})

// Estiliza as linhas da música (As notas que o usuário deve acertar)
function segmentStyle(seg) {
  const left = centerX.value + (seg.start - props.currentTime) * pxPerSec.value
  const width = Math.max((seg.end - seg.start) * pxPerSec.value, 2)
  const top = midiToY(seg.note)

  return {
    left: `${left}px`,
    width: `${width}px`,
    top: `${top}%`,
  }
}

// Estiliza a bolinha do usuário (Fixa em X no centro, flutua em Y)
const userBallStyle = computed(() => {
  const top = midiToY(props.userMidi)
  return {
    left: `${centerX.value}px`,
    top: `${top}%`,
  }
})

// Monitoramento da largura do componente para manter o centro perfeito
function updateWidth() {
  if (viewportRef.value) viewportWidth.value = viewportRef.value.clientWidth
}

let resizeObserver
onMounted(() => {
  updateWidth()
  resizeObserver = new ResizeObserver(updateWidth)
  if (viewportRef.value) resizeObserver.observe(viewportRef.value)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

watch(() => props.segments, updateWidth)
</script>

<style scoped>
.pitch-viewport {
  position: relative;
  height: 220px; /* Altura fixa ideal para a pista do jogo */
  background: #121212;
  border: 2px solid #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
  box-sizing: border-box;
}

/* Linha vertical central que indica o tempo atual */
.playhead-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(255, 255, 255, 0.15);
  border-left: 1px dashed rgba(255, 255, 255, 0.3);
  pointer-events: none;
  z-index: 1;
}

/* As linhas finas da melodia da música original */
.note-line {
  position: absolute;
  height: 8px; /* Espessura fixa elegante para a linha da música */
  background: linear-gradient(90deg, #00c6ff, #0072ff);
  border-radius: 4px;
  transform: translateY(-50%); /* Centraliza perfeitamente a linha na porcentagem Y */
  box-shadow: 0 0 6px rgba(0, 114, 255, 0.5);
  transition: background 0.3s;
}

/* A bolinha do cantor */
.user-ball {
  position: absolute;
  width: 14px;
  height: 14px;
  background: #ff0055;
  border: 2px solid #ffffff;
  border-radius: 50%;
  transform: translate(-50%, -50%); /* Garante que o centro da bola seja o ponto exato */
  box-shadow: 0 0 12px #ff0055, 0 0 4px #ff0055;
  z-index: 10;
  /* Transição ultra curta em CSS para suavizar pequenas variações do hardware */
  transition: top 0.04s linear, opacity 0.2s ease;
  opacity: 1;
}

/* Quando o usuário fica em silêncio, a bolinha apaga suavemente e fica cinza */
.user-ball.silent {
  background: #555555;
  border-color: #777777;
  box-shadow: none;
  opacity: 0.2;
}

.pitch-bar-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 220px;
  color: #888;
  font-family: sans-serif;
  background: #121212;
  border-radius: 8px;
}
</style>