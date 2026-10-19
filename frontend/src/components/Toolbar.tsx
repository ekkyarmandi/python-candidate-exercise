import type { FormEvent } from 'react'
import { Field } from './Field'
import type { StatusChoice } from '../types'

interface ToolbarProps {
  initialQuery: string
  initialStatus: string
  statusChoices: StatusChoice[]
  busy: boolean
  onSubmit: (values: { q: string; status: string }) => void
}

export function Toolbar({
  initialQuery,
  initialStatus,
  statusChoices,
  busy,
  onSubmit,
}: ToolbarProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    onSubmit({
      q: String(data.get('q') ?? '').trim(),
      status: String(data.get('status') ?? ''),
    })
  }

  return (
    <div className="toolbar">
      <form role="search" className="filters" onSubmit={handleSubmit}>
        <Field id="filter-q" label="Search contacts">
          <input
            id="filter-q"
            type="search"
            name="q"
            defaultValue={initialQuery}
            placeholder="Search name, company, email…"
            autoComplete="off"
            spellCheck={false}
          />
        </Field>
        <Field id="filter-status" label="Status">
          <select id="filter-status" name="status" defaultValue={initialStatus}>
            <option value="">All statuses</option>
            {statusChoices.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </Field>
        <button type="submit" className="btn" disabled={busy}>
          {busy ? 'Searching…' : 'Search'}
        </button>
      </form>
      <a className="export-link" href="/export/">
        Export CSV
      </a>
    </div>
  )
}
