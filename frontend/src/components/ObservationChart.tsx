import type { Observation } from '../types'

interface ObservationChartProps {
  observations: Observation[]
}

const WIDTH = 960
const HEIGHT = 370
const PADDING = { top: 24, right: 24, bottom: 56, left: 70 }
const GRID_ROWS = 4

function formatPeriod(period: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${period}T00:00:00Z`))
}

export function ObservationChart({ observations }: ObservationChartProps) {
  const values = observations.map((item) => item.anomaly)
  const valueSpan = Math.max(...values, 0) - Math.min(...values, 0)
  const padding = (valueSpan || 1) * 0.08
  const minimum = Math.min(...values, 0) - padding
  const maximum = Math.max(...values, 0) + padding
  const plotWidth = WIDTH - PADDING.left - PADDING.right
  const plotHeight = HEIGHT - PADDING.top - PADDING.bottom
  const x = (index: number) => PADDING.left + (observations.length === 1 ? plotWidth / 2 : (index / (observations.length - 1)) * plotWidth)
  const y = (value: number) => PADDING.top + ((maximum - value) / (maximum - minimum)) * plotHeight
  const path = observations
    .map((item, index) => `${index === 0 ? 'M' : 'L'} ${x(index).toFixed(2)} ${y(item.anomaly).toFixed(2)}`)
    .join(' ')
  const chartId = 'oni-chart'
  const firstPeriod = observations[0].period
  const lastPeriod = observations.at(-1)!.period

  return (
    <div className="chart-wrap">
      <svg
        className="observation-chart"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-labelledby={`${chartId}-title ${chartId}-description`}
      >
        <title id={`${chartId}-title`}>Courbe historique de l’anomalie ONI</title>
        <desc id={`${chartId}-description`}>
          {observations.length} observations mensuelles en degrés Celsius, de {firstPeriod} à {lastPeriod}.
        </desc>

        {Array.from({ length: GRID_ROWS + 1 }, (_, index) => {
          const value = maximum - ((maximum - minimum) * index) / GRID_ROWS
          const tickY = y(value)
          return (
            <g key={index} className="chart-grid">
              <line x1={PADDING.left} x2={WIDTH - PADDING.right} y1={tickY} y2={tickY} />
              <text x={PADDING.left - 12} y={tickY + 4} textAnchor="end">{value.toFixed(1)}</text>
            </g>
          )
        })}

        {minimum <= 0 && maximum >= 0 && (
          <line
            className="zero-line"
            x1={PADDING.left}
            x2={WIDTH - PADDING.right}
            y1={y(0)}
            y2={y(0)}
          />
        )}

        <path className="chart-line" d={path} />
        {observations.map((item, index) => (
          <circle
            className="chart-point"
            cx={x(index)}
            cy={y(item.anomaly)}
            key={`${item.period}-${item.season}`}
            r={observations.length > 120 ? 1.8 : 3.2}
          >
            <title>{formatPeriod(item.period)} · {item.season} · {item.anomaly.toFixed(2)} °C</title>
          </circle>
        ))}

        <text className="axis-label" x={PADDING.left} y={HEIGHT - 18}>{firstPeriod.slice(0, 7)}</text>
        <text className="axis-label" x={WIDTH - PADDING.right} y={HEIGHT - 18} textAnchor="end">
          {lastPeriod.slice(0, 7)}
        </text>
      </svg>
    </div>
  )
}
