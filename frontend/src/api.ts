import type { EpisodeComparison, EpisodePeriod, EpisodeSummary, Observation, PeriodRange } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin

function isObservation(value: unknown): value is Observation {
  if (typeof value !== 'object' || value === null) return false
  const item = value as Record<string, unknown>
  return (
    typeof item.period === 'string' &&
    /^\d{4}-\d{2}-\d{2}$/.test(item.period) &&
    typeof item.season === 'string' &&
    typeof item.total === 'number' &&
    Number.isFinite(item.total) &&
    typeof item.anomaly === 'number' &&
    Number.isFinite(item.anomaly)
  )
}

function isObservationList(value: unknown): value is Observation[] {
  return Array.isArray(value) && value.every(isObservation)
}

function isEpisodeSummary(value: unknown): value is EpisodeSummary {
  if (typeof value !== 'object' || value === null) return false
  const item = value as Record<string, unknown>
  return (
    typeof item.start_date === 'string' &&
    typeof item.end_date === 'string' &&
    typeof item.observation_count === 'number' &&
    typeof item.mean_anomaly === 'number' &&
    typeof item.maximum_anomaly === 'number' &&
    typeof item.maximum_period === 'string' &&
    typeof item.minimum_anomaly === 'number' &&
    typeof item.minimum_period === 'string'
  )
}

function isEpisodeComparison(value: unknown): value is EpisodeComparison {
  if (typeof value !== 'object' || value === null) return false
  const item = value as Record<string, unknown>
  return (
    isEpisodeSummary(item.first) &&
    isEpisodeSummary(item.second) &&
    typeof item.mean_anomaly_difference === 'number' &&
    typeof item.interpretation === 'string' &&
    Array.isArray(item.caveats) &&
    item.caveats.every((caveat) => typeof caveat === 'string')
  )
}

export async function fetchObservations(
  range: PeriodRange,
  signal?: AbortSignal,
): Promise<Observation[]> {
  const url = new URL('/api/v1/observations', API_BASE_URL)
  if (range.startDate) url.searchParams.set('start_date', range.startDate)
  if (range.endDate) url.searchParams.set('end_date', range.endDate)

  const response = await fetch(url, { signal })
  if (!response.ok) {
    throw new Error(`L’API n’a pas pu charger les données (HTTP ${response.status}).`)
  }

  const payload: unknown = await response.json()
  if (!isObservationList(payload)) {
    throw new Error('La réponse de l’API ne respecte pas le format attendu.')
  }

  return payload
}

export async function fetchEpisodeComparison(
  first: EpisodePeriod,
  second: EpisodePeriod,
  signal?: AbortSignal,
): Promise<EpisodeComparison> {
  const url = new URL('/api/v1/comparisons', API_BASE_URL)
  url.searchParams.set('first_start_date', `${first.startMonth}-01`)
  url.searchParams.set('first_end_date', `${first.endMonth}-01`)
  url.searchParams.set('second_start_date', `${second.startMonth}-01`)
  url.searchParams.set('second_end_date', `${second.endMonth}-01`)

  const response = await fetch(url, { signal })
  if (!response.ok) {
    throw new Error(`La comparaison a échoué (HTTP ${response.status}).`)
  }

  const payload: unknown = await response.json()
  if (!isEpisodeComparison(payload)) {
    throw new Error('La réponse de comparaison ne respecte pas le format attendu.')
  }

  return payload
}
