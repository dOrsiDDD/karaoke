import { ref } from 'vue'
import { addSongToBackend, fetchSongSegments } from './useKaraokeApi'

export function useSongQueue() {
  const currentVideoId = ref(null)
  const currentSong = ref(null)
  const upNext = ref([])
  const segments = ref([])

  async function prepareSongItem(item) {
    if (!item.syncOffset && item.syncOffset !== 0) {
      item.syncOffset = 0
    }

    if (item.segments) {
      segments.value = item.segments
      currentSong.value = item
      return
    }

    if (item.addPromise) {
      const data = await item.addPromise
      if (data?.details?.segments) {
        item.segments = data.details.segments
        item.syncOffset = data.details.syncOffset ?? 0
        segments.value = item.segments
        currentSong.value = item
        return
      }
    }

    const fetched = await fetchSongSegments(item.karaokeVideoId)
    item.segments = fetched?.segments ?? []
    item.syncOffset = Number(fetched?.syncOffset ?? 0)
    segments.value = item.segments
    currentSong.value = item
  }

  async function addSong(song) {
    const karaokeVideoId = song.karaokeVideoId 
    const formatted = {
      title: song.title,
      karaokeVideoId: karaokeVideoId,
      query: song.query,
      segments: song.segments ?? null,
      syncOffset: song.syncOffset ?? 0,
      addPromise: null,
      isCatalogSong: song.source === 'catalog',
    }

    const alreadyInQueue = upNext.value.some(
      (q) => q.karaokeVideoId === formatted.karaokeVideoId
    )
    if (alreadyInQueue) return

    if (!formatted.isCatalogSong) {
      formatted.addPromise = addSongToBackend(song).catch((err) => {
        console.error('Erro ao adicionar música ao backend:', err)
        return null
      })
    }

    upNext.value.push(formatted)

    if (!currentVideoId.value) {
      currentVideoId.value = formatted.karaokeVideoId
      await prepareSongItem(formatted)
    }
  }

  async function advanceQueue() {
    upNext.value.shift()
    const next = upNext.value[0]
    currentVideoId.value = next?.karaokeVideoId ?? null
    if (next) {
      await prepareSongItem(next)
    } else {
      segments.value = []
      currentSong.value = null
    }
  }

  return {
    currentVideoId,
    currentSong,
    upNext,
    segments,
    addSong,
    advanceQueue,
    prepareSongItem,
  }
}
