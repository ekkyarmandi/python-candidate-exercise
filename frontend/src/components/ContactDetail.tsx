import { formatMoney } from '../lib/format'
import { ActivityFeed } from './ActivityFeed'
import { DeleteAction } from './DeleteAction'
import { NoteForm } from './NoteForm'
import { StatusForm } from './StatusForm'
import type { Detail, StatusChoice } from '../types'

interface ContactDetailProps {
  detail: Detail
  statusChoices: StatusChoice[]
  onChangeStatus: (newStatus: string) => Promise<void>
  onAddNote: (note: string) => Promise<void>
  onDelete: () => Promise<void>
}

export function ContactDetail({
  detail,
  statusChoices,
  onChangeStatus,
  onAddNote,
  onDelete,
}: ContactDetailProps) {
  const contact = detail.contact

  return (
    <div className="detail">
      <h3 className="truncate">{contact.name}</h3>
      <dl>
        <dt>Company</dt>
        <dd>{contact.company || '—'}</dd>
        <dt>Email</dt>
        <dd className="truncate">{contact.email || '—'}</dd>
        <dt>Phone</dt>
        <dd>{contact.phone || '—'}</dd>
        <dt>Owner</dt>
        <dd>{contact.owner || '—'}</dd>
        <dt>Value</dt>
        <dd className="num">{formatMoney(contact.value)}</dd>
      </dl>
      <StatusForm
        contact={contact}
        statusChoices={statusChoices}
        onSave={onChangeStatus}
      />
      <NoteForm onSave={onAddNote} />
      <DeleteAction contact={contact} onDelete={onDelete} />
      <h4>Activity</h4>
      <ActivityFeed activities={detail.activities} />
    </div>
  )
}
