export default function StatusBar({ status }) {
  return (
    <header className="statusbar">
      <div className="brand">
        <span className="brand-mark">EGFR</span>
        <span className="brand-name">Inhibitor Discovery</span>
      </div>
      <div className="metrics">
        <Metric label="molecules" value={status.n_molecules.toLocaleString()} />
        <Metric label="RMSE" value={status.rmse} />
        <Metric label="MAE" value={status.mae} />
        <Metric label="R²" value={status.r2} />
      </div>
    </header>
  )
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span className="metric-value">{value}</span>
      <span className="metric-label">{label}</span>
    </div>
  )
}
