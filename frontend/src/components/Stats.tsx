import { formatMoney } from '../lib/format'
import type { Summary } from '../types'

interface StatsProps {
  summary: Summary
}

export function Stats({ summary }: StatsProps) {
  return (
    <div className="stats">
      <div className="stat">
        <b>{summary.total}</b>
        <div className="muted">All contacts</div>
      </div>
      <div className="stat">
        <b>{formatMoney(summary.pipeline)}</b>
        <div className="muted">Pipeline value</div>
      </div>
    </div>
  )
}
