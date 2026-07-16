const BASE = '/api'

async function getJSON(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`Request to ${path} failed (${res.status})`)
  return res.json()
}

export function getStatus() {
  return getJSON('/status')
}

export function getEda() {
  return getJSON('/eda')
}

export function getTrainingCurve() {
  return getJSON('/training-curve')
}

export function getCandidates(topN = 8) {
  return getJSON(`/candidates?top_n=${topN}`)
}

export async function regenerate(topN = 8) {
  const res = await fetch(`${BASE}/generate?top_n=${topN}`, { method: 'POST' })
  if (!res.ok) throw new Error('Generation failed')
  return res.json()
}

export function structureUrl(smiles) {
  return `${BASE}/structure?smiles=${encodeURIComponent(smiles)}`
}
