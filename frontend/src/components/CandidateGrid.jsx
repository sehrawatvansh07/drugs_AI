import CandidateCard from './CandidateCard'

export default function CandidateGrid({ candidates }) {
  if (!candidates.length) {
    return <p className="empty-state">No candidates yet — try generating a new batch.</p>
  }

  return (
    <div className="candidate-grid">
      {candidates.map((c) => (
        <CandidateCard key={c.SMILES} candidate={c} />
      ))}
    </div>
  )
}
