import { ReferenceArea, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'

export default function PotencyScatter({ candidates }) {
  const data = candidates.map((c) => ({
    x: c.QED_DrugLikeness,
    y: c.Predicted_pIC50,
    smiles: c.SMILES,
    usefulness: c.Usefulness_Index,
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
        <XAxis
          type="number"
          dataKey="x"
          domain={[0.2, 1]}
          name="QED"
          tick={{ fontSize: 10, fill: 'var(--text-secondary)' }}
        />
        <YAxis
          type="number"
          dataKey="y"
          domain={[4, 10]}
          name="pIC50"
          tick={{ fontSize: 10, fill: 'var(--text-secondary)' }}
        />
        <ZAxis range={[80, 80]} />
        <ReferenceArea
          x1={0.6}
          x2={1.0}
          y1={8.0}
          y2={10}
          fill="var(--accent-qed)"
          fillOpacity={0.08}
          stroke="var(--accent-qed)"
          strokeDasharray="4 4"
        />
        <Tooltip
          cursor={{ strokeDasharray: '3 3' }}
          contentStyle={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
          }}
        />
        <Scatter data={data} fill="var(--accent-potency)" />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
