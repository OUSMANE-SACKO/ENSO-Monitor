import { useEffect, useState, type FormEvent } from 'react'
import { fetchEpisodeComparison, fetchObservations } from './api'
import { ObservationChart } from './components/ObservationChart'
import { PeriodFilter } from './components/PeriodFilter'
import type { EpisodeComparison, EpisodePeriod, Observation, PeriodRange } from './types'
import './App.css'

const EMPTY_RANGE: PeriodRange = { startDate: '', endDate: '' }
const EMPTY_EPISODE: EpisodePeriod = { startMonth: '', endMonth: '' }

interface ComparisonPeriods {
  first: EpisodePeriod
  second: EpisodePeriod
}

interface EpisodeResultProps {
  label: string
  summary: EpisodeComparison['first']
}

function formatAnomaly(value: number): string {
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function EpisodeResult({ label, summary }: EpisodeResultProps) {
  return (
    <article className="episode-result" aria-label={`Résumé ${label}`}>
      <div className="episode-result-heading">
        <h3>{label}</h3>
        <span>{summary.observation_count} obs.</span>
      </div>
      <p className="episode-dates">{summary.start_date} → {summary.end_date}</p>
      <dl>
        <div>
          <dt>Anomalie moyenne</dt>
          <dd>{formatAnomaly(summary.mean_anomaly)} °C</dd>
        </div>
        <div>
          <dt>Maximum observé</dt>
          <dd>{formatAnomaly(summary.maximum_anomaly)} °C <span>· {summary.maximum_period}</span></dd>
        </div>
        <div>
          <dt>Minimum observé</dt>
          <dd>{formatAnomaly(summary.minimum_anomaly)} °C <span>· {summary.minimum_period}</span></dd>
        </div>
      </dl>
    </article>
  )
}

function App() {
  const [draftRange, setDraftRange] = useState<PeriodRange>(EMPTY_RANGE)
  const [appliedRange, setAppliedRange] = useState<PeriodRange>(EMPTY_RANGE)
  const [observations, setObservations] = useState<Observation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [comparisonPeriods, setComparisonPeriods] = useState<ComparisonPeriods>({
    first: EMPTY_EPISODE,
    second: EMPTY_EPISODE,
  })
  const [comparison, setComparison] = useState<EpisodeComparison | null>(null)
  const [comparisonLoading, setComparisonLoading] = useState(false)
  const [comparisonError, setComparisonError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    fetchObservations(appliedRange, controller.signal)
      .then(setObservations)
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setError(cause instanceof Error ? cause.message : 'Une erreur inattendue est survenue.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [appliedRange])

  function applyPeriod(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (draftRange.startDate && draftRange.endDate && draftRange.startDate > draftRange.endDate) {
      setError('La date de début doit précéder ou être égale à la date de fin.')
      return
    }

    setLoading(true)
    setError(null)
    setAppliedRange({ ...draftRange })
  }

  function updateEpisodePeriod(
    episode: keyof ComparisonPeriods,
    field: keyof EpisodePeriod,
    value: string,
  ) {
    setComparisonPeriods((current) => ({
      ...current,
      [episode]: { ...current[episode], [field]: value },
    }))
  }

  async function comparePeriods(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const { first, second } = comparisonPeriods
    if (
      first.startMonth > first.endMonth ||
      second.startMonth > second.endMonth
    ) {
      setComparisonError('Chaque date de début doit précéder ou être égale à sa date de fin.')
      return
    }

    setComparison(null)
    setComparisonError(null)
    setComparisonLoading(true)
    try {
      setComparison(await fetchEpisodeComparison(first, second))
    } catch (cause: unknown) {
      setComparisonError(cause instanceof Error ? cause.message : 'La comparaison a échoué.')
    } finally {
      setComparisonLoading(false)
    }
  }

  const latestObservation = observations.at(-1)

  return (
    <main className="app-shell">
      <header className="site-header">
        <a className="brand" href="#main-content" aria-label="ENSO Monitor, accueil">
          <span className="brand-mark" aria-hidden="true">E</span>
          <span>ENSO <strong>MONITOR</strong></span>
        </a>
        <span className="header-source">Données NOAA · Centre de prévision climatique</span>
      </header>

      <div id="main-content" className="dashboard">
        <section className="intro" aria-labelledby="page-title">
          <p className="eyebrow">CLIMAT · PACIFIQUE ÉQUATORIAL</p>
          <h1 id="page-title">Suivre le rythme<br />d’El Niño et La Niña.</h1>
          <p className="intro-copy">
            Explorez l’indice ONI historique et comparez les variations de température
            dans la région Niño 3.4.
          </p>
          <div className="index-chip">
            <span className="status-dot" aria-hidden="true" />
            <span><strong>ONI</strong> · Oceanic Niño Index</span>
          </div>
        </section>

        <section className="data-panel" aria-labelledby="series-title">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">SÉRIE TEMPORELLE</p>
              <h2 id="series-title">Anomalie ONI</h2>
            </div>
            <div className="unit-label">Anomalie · °C</div>
          </div>

          <PeriodFilter
            range={draftRange}
            loading={loading}
            onChange={setDraftRange}
            onSubmit={applyPeriod}
          />

          {error && <p className="alert" role="alert">{error}</p>}
          {loading && <p className="status-message" role="status">Chargement des observations NOAA…</p>}
          {!loading && !error && observations.length === 0 && (
            <p className="status-message" role="status">Aucune observation pour cette période.</p>
          )}
          {!error && observations.length > 0 && (
            <>
              <p className="chart-summary" aria-live="polite">
                {observations.length} observation{observations.length > 1 ? 's' : ''} affichée{observations.length > 1 ? 's' : ''}
                {latestObservation && (
                  <span> · Dernière valeur : <strong>{latestObservation.anomaly.toFixed(2)} °C</strong></span>
                )}
              </p>
              <ObservationChart observations={observations} />
            </>
          )}

          <footer className="panel-footer">
            <span>Source : NOAA CPC · Indice ONI · région Niño 3.4</span>
            <span>Valeurs en degrés Celsius (°C)</span>
          </footer>
        </section>

        <section className="comparison-panel" aria-labelledby="comparison-title">
          <div className="comparison-intro">
            <p className="eyebrow">LECTURE COMPARATIVE</p>
            <h2 id="comparison-title">Comparer deux périodes historiques</h2>
            <p>
              Choisissez les bornes mensuelles. Les statistiques décrivent les observations ONI
              disponibles, sans attribuer automatiquement une classe climatique.
            </p>
          </div>

          <form className="comparison-form" onSubmit={comparePeriods}>
            {(['first', 'second'] as const).map((episode, index) => (
              <fieldset key={episode}>
                <legend>Période {index === 0 ? 'A' : 'B'}</legend>
                <label>
                  <span>Du mois</span>
                  <input
                    required
                    type="month"
                    value={comparisonPeriods[episode].startMonth}
                    max={comparisonPeriods[episode].endMonth || undefined}
                    onChange={(event) => updateEpisodePeriod(episode, 'startMonth', event.target.value)}
                  />
                </label>
                <label>
                  <span>Au mois</span>
                  <input
                    required
                    type="month"
                    value={comparisonPeriods[episode].endMonth}
                    min={comparisonPeriods[episode].startMonth || undefined}
                    onChange={(event) => updateEpisodePeriod(episode, 'endMonth', event.target.value)}
                  />
                </label>
              </fieldset>
            ))}
            <button type="submit" disabled={comparisonLoading}>
              {comparisonLoading ? 'Comparaison…' : 'Comparer les périodes'}
            </button>
          </form>

          {comparisonError && <p className="alert" role="alert">{comparisonError}</p>}
          {comparison && (
            <div className="comparison-result" aria-live="polite">
              <div className="episode-results">
                <EpisodeResult label="Période A" summary={comparison.first} />
                <EpisodeResult label="Période B" summary={comparison.second} />
              </div>
              <p className="interpretation">
                <strong>Interprétation mesurée</strong>
                {comparison.interpretation}
              </p>
              <div className="caveats">
                <h3>À garder en tête</h3>
                <ul>
                  {comparison.caveats.map((caveat) => <li key={caveat}>{caveat}</li>)}
                </ul>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  )
}

export default App
