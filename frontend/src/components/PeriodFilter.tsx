import type { FormEvent } from 'react'
import type { PeriodRange } from '../types'

interface PeriodFilterProps {
  range: PeriodRange
  loading: boolean
  onChange: (range: PeriodRange) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

export function PeriodFilter({ range, loading, onChange, onSubmit }: PeriodFilterProps) {
  return (
    <form className="period-filter" onSubmit={onSubmit}>
      <label>
        <span>Du</span>
        <input
          type="date"
          value={range.startDate}
          max={range.endDate || undefined}
          onChange={(event) => onChange({ ...range, startDate: event.target.value })}
        />
      </label>
      <label>
        <span>Au</span>
        <input
          type="date"
          value={range.endDate}
          min={range.startDate || undefined}
          onChange={(event) => onChange({ ...range, endDate: event.target.value })}
        />
      </label>
      <button type="submit" disabled={loading}>Appliquer la période</button>
    </form>
  )
}
