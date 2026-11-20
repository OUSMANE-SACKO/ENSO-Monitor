import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

const observations = [
  { period: '1997-01-01', season: 'DJF', total: 26.4, anomaly: 0.4 },
  { period: '1997-02-01', season: 'JFM', total: 27.1, anomaly: 1.1 },
  { period: '1997-03-01', season: 'FMA', total: 28.0, anomaly: 2.0 },
]

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('tableau de bord ENSO', () => {
  it('met à jour la courbe et les valeurs après un changement de période', async () => {
    const fetchMock = vi.fn<typeof fetch>(async (input) => {
      const url = new URL(String(input))
      const filtered = url.searchParams.has('start_date')
        ? observations.slice(1)
        : observations
      return jsonResponse(filtered)
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    render(<App />)
    await screen.findByText(/3 observations affichées/)

    const startDate = screen.getByLabelText('Du')
    await user.type(startDate, '1997-02-01')
    await user.click(screen.getByRole('button', { name: 'Appliquer la période' }))

    await screen.findByText(/2 observations affichées/)
    await waitFor(() => {
      const chart = screen.getByRole('img', { name: /Courbe historique de l’anomalie ONI/ })
      expect(chart.querySelectorAll('circle')).toHaveLength(2)
    })
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ search: '?start_date=1997-02-01' }),
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )
  })
})
