import { useCallback, useEffect, useState } from 'react'
import StatusBar from './components/StatusBar'
import EdaChart from './components/EdaChart'
import CandidateGrid from './components/CandidateGrid'
import PotencyScatter from './components/PotencyScatter'
import { getCandidates, getEda, getStatus, regenerate } from './api'

export default function App() {
  const [status, setStatus] = useState(null)
  const [eda, setEda] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [regenerating, setRegenerating] = useState(false)
  const [error, setError] = useState(null)

  const loadAll = useCallback(async () => {
    try {
      setLoading(true)
      const [s, e, c] = await Promise.all([getStatus(), getEda(), getCandidates(8)])
      setStatus(s)
      setEda(e)
      setCandidates(c)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const handleRegenerate = async () => {
    try {
      setRegenerating(true)
      const c = await regenerate(8)
      setCandidates(c)
    } catch (err) {
      setError(err.message)
    } finally {
      setRegenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-pulse" />
        <p>Training the potency model and preparing the assay data…</p>
        <p className="hint">First load only — this runs the same 50-epoch training as the notebook.</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="loading-screen error">
        <p>Couldn't reach the backend.</p>
        <p className="hint">{error} — make sure uvicorn is running on port 8000.</p>
      </div>
    )
  }

  return (
    <div className="app">
      <StatusBar status={status} />
      <main className="layout">
        <section className="panel eda-panel">
          <h2>Bioactivity landscape</h2>
          <p className="panel-sub">
            {eda.total.toLocaleString()} EGFR compounds, deduplicated to a single median pIC50 each.
          </p>
          <EdaChart eda={eda} />
        </section>

        <section className="panel scatter-panel">
          <h2>Potency vs. drug-likeness</h2>
          <p className="panel-sub">Every candidate from the current batch, scored by the trained model.</p>
          <PotencyScatter candidates={candidates} />
        </section>

        <section className="panel candidates-panel">
          <div className="candidates-header">
            <div>
              <h2>Top generated candidates</h2>
              <p className="panel-sub">BRICS-assembled from the training set's most potent molecules.</p>
            </div>
            <button className="btn-generate" onClick={handleRegenerate} disabled={regenerating}>
              {regenerating ? 'Generating…' : 'Generate new candidates'}
            </button>
          </div>
          <CandidateGrid candidates={candidates} />
        </section>
      </main>
    </div>
  )
}
