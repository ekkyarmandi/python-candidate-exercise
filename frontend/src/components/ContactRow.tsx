import type { MouseEvent } from 'react'
import { formatMoney } from '../lib/format'
import { buildRowHref } from '../lib/url'
import type { Contact } from '../types'

interface ContactRowProps {
  contact: Contact
  selected: boolean
  query: string
  status: string
  onSelect: (contactId: number, event: MouseEvent<HTMLAnchorElement>) => void
}

export function ContactRow({
  contact,
  selected,
  query,
  status,
  onSelect,
}: ContactRowProps) {
  return (
    <a
      className={'row' + (selected ? ' selected' : '')}
      href={buildRowHref({ q: query, status }, contact.id)}
      aria-current={selected ? 'true' : undefined}
      onClick={(event) => onSelect(contact.id, event)}
    >
      <span className="row__main">
        <b className="truncate">{contact.name}</b>
        <div className="muted truncate">{contact.email}</div>
      </span>
      <span className="truncate">{contact.company}</span>
      <span>
        <span className="pill">{contact.status_label}</span>
      </span>
      <span className="num">{formatMoney(contact.value)}</span>
    </a>
  )
}
