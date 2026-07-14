<template>
  <div class="pitch-bar" v-if="segments.length">
    <div ref="viewportRef" class="pitch-viewport">

      <div class="playhead-line" :style="{ left: `${centerX}px` }" />

      <svg
        v-if="melodyPath"
        class="melody-svg"
        xmlns="http://www.w3.org/2000/svg"
        :width="viewportWidth"
        :height="viewportHeight"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="melodyGradient" x1="0" x2="1">
            <stop offset="0%" stop-color="#00c6ff" />
            <stop offset="100%" stop-color="#0072ff" />
          </linearGradient>
        </defs>

        <path
          :d="melodyPath"
          class="melody-path"
          fill="none"
          :stroke="pathStroke"
          stroke-width="5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>

      <div
        class="user-ball"
        :class="{ silent: !isVoiced || userMidi == null, 'hit-glow': isHittingNote }"
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
  syncOffset: { type: Number, default: 0 },
})

const WINDOW_SEC = 6 // Quantos segundos de música aparecem na tela
const viewportRef = ref(null)
const viewportWidth = ref(600)
const viewportHeight = ref(140)

const pxPerSec = computed(() => viewportWidth.value / WINDOW_SEC)
const centerX = computed(() => viewportWidth.value / 2)

// --- FILTRO DE DURAÇÃO (Noise Reduction) ---
// Remove segmentos muito curtos (ex.: ruído)
const cleanedSegments = computed(() => {
  return props.segments.filter((s) => (s.end - s.start) >= 0.15)
})

// Aplica ajuste de sincronia ao desenho da melodia
const syncedSegments = computed(() => {
  return cleanedSegments.value.map((seg) => ({
    ...seg,
    start: seg.start + props.syncOffset,
    end: seg.end + props.syncOffset,
  }))
})

// --- LIMITES DINÂMICOS DA MÚSICA (usando cleanedSegments) ---
const MIN_MIDI = computed(() => {
  if (!cleanedSegments.value.length) return 50
  return Math.min(...cleanedSegments.value.map((s) => s.note)) - 3
})

const MAX_MIDI = computed(() => {
  if (!cleanedSegments.value.length) return 80
  return Math.max(...cleanedSegments.value.map((s) => s.note)) + 3
})

const midiRange = computed(() => {
  const range = MAX_MIDI.value - MIN_MIDI.value
  return range <= 0 ? 1 : range
})

// Converte MIDI para posição Y em porcentagem (0% topo, 100% fundo)
function midiToY(midi) {
  if (midi == null) return 50
  const clamped = Math.max(MIN_MIDI.value, Math.min(MAX_MIDI.value, midi))
  return ((MAX_MIDI.value - clamped) / midiRange.value) * 100
}

// Converte MIDI para Y em pixels (para usar no SVG)
function midiToYPx(midi) {
  const pct = midiToY(midi)
  return (pct / 100) * viewportHeight.value
}

// Segments visíveis na janela atual (baseado em syncedSegments)
const visibleSegments = computed(() => {
  const half = WINDOW_SEC / 2
  const t0 = props.currentTime - half
  const t1 = props.currentTime + half
  return syncedSegments.value.filter((s) => s.end > t0 && s.start < t1)
})

// Path SVG que desenha notas como linhas horizontais e conecta notas
const melodyPath = computed(() => {
  const segs = visibleSegments.value
  if (!segs.length) return ''

  const MAX_CONNECT_GAP = 0.3 // segundos
  const parts = []

  for (let i = 0; i < segs.length; i++) {
    const seg = segs[i]
    const x1 = centerX.value + (seg.start - props.currentTime) * pxPerSec.value
    const x2 = centerX.value + (seg.end - props.currentTime) * pxPerSec.value
    const y = midiToYPx(seg.note)

    const gapFromPrev = i > 0 ? seg.start - segs[i - 1].end : Infinity

    // Começa nova frase (levanta a caneta) se for a primeira nota
    // ou se o gap desde a nota anterior for maior que MAX_CONNECT_GAP
    if (i === 0 || gapFromPrev > MAX_CONNECT_GAP) {
      parts.push(`M ${x1.toFixed(2)} ${y.toFixed(2)}`)
    }

    // Linha horizontal da própria nota (start -> end)
    parts.push(`L ${x2.toFixed(2)} ${y.toFixed(2)}`)

    // Decide se conecta ao início da próxima nota (slide) com base no gap
    const next = segs[i + 1]
    if (next) {
      const gapToNext = next.start - seg.end
      if (gapToNext <= MAX_CONNECT_GAP) {
        const nx1 = centerX.value + (next.start - props.currentTime) * pxPerSec.value
        const ny = midiToYPx(next.note)
        parts.push(`L ${nx1.toFixed(2)} ${ny.toFixed(2)}`)
      }
      // Se gapToNext > MAX_CONNECT_GAP -> não conectar (próxima iteração emitirá `M`)
    }
  }

  return parts.join(' ')
})

// Bolinha do usuário posicionada em pixels sobre o SVG
const userBallStyle = computed(() => {
  const topPx = midiToYPx(props.userMidi)
  return {
    left: `${centerX.value}px`,
    top: `${topPx}px`,
  }
})

// Verifica se o usuário está no intervalo de uma nota visível e na margem de tolerância
const isHittingNote = computed(() => {
  if (!props.isVoiced || props.userMidi == null) return false

  const current = visibleSegments.value.find((seg) => {
    return props.currentTime >= seg.start && props.currentTime <= seg.end
  })

  if (!current) return false
  return Math.abs(props.userMidi - current.note) <= 1
})

const pathStroke = computed(() => {
  return isHittingNote.value ? '#4ade80' : 'url(#melodyGradient)'
})

// Monitoramento da largura/altura do componente para manter o centro perfeito
function updateWidth() {
  if (viewportRef.value) {
    viewportWidth.value = viewportRef.value.clientWidth
    viewportHeight.value = viewportRef.value.clientHeight
  }
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
  height: 140px; /* Altura fixa ideal para a pista do jogo */
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

.melody-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.melody-path {
  filter: drop-shadow(0 0 8px rgba(0, 114, 255, 0.45));
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
  transition: top 0.04s linear, opacity 0.2s ease, transform 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
  opacity: 1;
}

.user-ball.hit-glow {
  background: #4ade80;
  border-color: #86efac;
  box-shadow: 0 0 20px rgba(74, 222, 128, 0.9), 0 0 28px rgba(74, 222, 128, 0.35);
  transform: translate(-50%, -50%) scale(1.2);
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
  height: 140px;
  color: #888;
  font-family: sans-serif;
  background: #121212;
  border-radius: 8px;
}
</style>