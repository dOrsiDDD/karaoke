const API_BASE = 'http://localhost:8000'

export async function searchKaraoke(query) {
  const res = await fetch(`${API_BASE}/karaoke_yt_search?q=${encodeURIComponent(query)}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail ?? 'Erro na busca')
  return data.results?.results ?? data.results ?? []
}

export async function searchCatalog(query) {
  const res = await fetch(`${API_BASE}/search_song_db?q=${encodeURIComponent(query)}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail ?? 'Erro na busca no catálogo')
  return data.songs ?? []
}

export async function addSongToBackend(song) {
  const formData = new FormData()
  formData.append('karaokeVideoId', song.karaokeVideoId)
  formData.append('title', song.title)
  formData.append('query', song.query)

  const res = await fetch(`${API_BASE}/add_song`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function fetchSongSegments(karaokeVideoId) {
  const res = await fetch(`${API_BASE}/song/${karaokeVideoId}`)
  if (!res.ok) return null
  const data = await res.json()
  return data.segments ?? null
}

export async function analyzeRecording(karaokeVideoId, blob) {
  const formData = new FormData()
  formData.append('karaokeVideoId', karaokeVideoId)
  formData.append('user_audio', blob)

  const res = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: formData })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail ?? data.message ?? 'Erro na análise')
  return data.score
}
