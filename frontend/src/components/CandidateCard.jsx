import { structureUrl } from '../api'

export default function CandidateCard({ candidate }) {
  // pIC50 typically falls in ~4-10 for this dataset; scale for the bar display only.
  const potencyPct = Math.min(Math.max((candidate.Predicted_pIC50 - 4) / 6, 0), 1) * 100
  const qedPct = candidate.QED_DrugLikeness * 100

  return (
    <div className="candidate-card">
      <img
        className="candidate-structure"
        src={structureUrl(candidate.SMILES)}
        alt="Generated molecule structure"
        loading="lazy"
      />
      <div className="candidate-bars">
        <Bar label="Potency" pct={potencyPct} value={candidate.Predicted_pIC50} colorVar="--accent-potency" />
        <Bar label="QED" pct={qedPct} value={candidate.QED_DrugLikeness} colorVar="--accent-qed" />
      </div>
      <div className="candidate-footer">Usefulness {candidate.Usefulness_Index}</div>
    </div>
  )
}

function Bar({ label, pct, value, colorVar }) {
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%`, background: `var(${colorVar})` }} />
      </div>
      <span className="bar-value">{value}</span>
    </div>
  )
}
