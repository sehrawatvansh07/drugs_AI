import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export default function EdaChart({ eda }) {
  const data = eda.bins.map((b, i) => ({ bin: b.toFixed(1), count: eda.counts[i] }))

  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <XAxis dataKey="bin" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} interval={4} />
          <YAxis tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
          <Tooltip
            contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', fontFamily: 'var(--font-mono)', fontSize: 12 }}
            labelStyle={{ color: 'var(--text-primary)' }}
          />
          <Bar dataKey="count" fill="var(--accent-potency)" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <p className="eda-footnote">
        {eda.active_count.toLocaleString()} molecules ({eda.active_pct}%) are highly active — pIC50 above 7.0
      </p>
    </div>
  )
}
