const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

export function toPitchClass(note) {
  if (note == null || Number.isNaN(note) || note < 0) return null
  return ((Math.round(note) % 12) + 12) % 12
}

export function pitchClassToNoteName(note) {
  const pitchClass = toPitchClass(note)
  return pitchClass == null ? '' : NOTE_NAMES[pitchClass]
}

export function midiToNoteName(midi) {
  if (midi == null || Number.isNaN(midi)) return ''
  const pitchClass = toPitchClass(midi)
  const octave = Math.floor(Math.round(midi) / 12) - 1
  return `${NOTE_NAMES[pitchClass]}${octave}`
}

export function freqToMidi(freq) {
  if (!freq || freq <= 0) return null
  return 69 + 12 * Math.log2(freq / 440)
}

/** Alinha o MIDI do usuário à oitava da nota de referência (pontuação usa apenas pitch class). */
export function adjustMidiToOctave(userMidi, referenceMidi) {
  if (userMidi == null || referenceMidi == null) return null
  const pitchClass = ((Math.round(userMidi) % 12) + 12) % 12
  const refOctave = Math.floor(referenceMidi / 12)
  return refOctave * 12 + pitchClass
}

export function segmentAtTime(segments, time) {
  if (!segments?.length) return null
  return segments.find((s) => time >= s.start && time < s.end) ?? null
}
