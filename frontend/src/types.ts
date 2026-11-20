export interface Observation {
  period: string
  season: string
  total: number
  anomaly: number
}

export interface PeriodRange {
  startDate: string
  endDate: string
}

export interface EpisodePeriod {
  startMonth: string
  endMonth: string
}

export interface EpisodeSummary {
  start_date: string
  end_date: string
  observation_count: number
  mean_anomaly: number
  maximum_anomaly: number
  maximum_period: string
  minimum_anomaly: number
  minimum_period: string
}

export interface EpisodeComparison {
  first: EpisodeSummary
  second: EpisodeSummary
  mean_anomaly_difference: number
  interpretation: string
  caveats: string[]
}
