import { formatDate } from '../lib/format'
import type { Activity } from '../types'

interface ActivityFeedProps {
  activities: Activity[]
}

export function ActivityFeed({ activities }: ActivityFeedProps) {
  if (activities.length === 0) {
    return <p className="muted">No activity yet.</p>
  }

  return (
    <ol className="activity">
      {activities.map((activity) => (
        <li key={activity.created_at_iso + activity.body}>
          <span className="pill">{activity.kind}</span>
          <span>{activity.body}</span>
          <div className="muted">
            {formatDate(activity.created_at_iso)} · {activity.created_by}
          </div>
        </li>
      ))}
    </ol>
  )
}
