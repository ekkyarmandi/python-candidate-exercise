import { useForm } from '@inertiajs/react'
import { useEffect, type FormEvent } from 'react'

import type { ContactStatus, DashboardFilters, StatusChoice } from '../types'

interface StatusFormProps {
  contactId: number
  currentStatus: ContactStatus
  filters: DashboardFilters
  statusChoices: StatusChoice[]
}

export default function StatusForm({
  contactId,
  currentStatus,
  filters,
  statusChoices,
}: StatusFormProps) {
  const form = useForm({ new_status: currentStatus })

  useEffect(() => {
    form.setData('new_status', currentStatus)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contactId])

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    form.transform((data) => ({ ...data, q: filters.q, status: filters.status }))
    form.patch(`/contacts/${contactId}/status/`, { preserveScroll: true })
  }

  return (
    <form onSubmit={submit}>
      <select
        name="new_status"
        value={form.data.new_status}
        onChange={(event) => form.setData('new_status', event.target.value as ContactStatus)}
      >
        {statusChoices.map((choice) => (
          <option key={choice.value} value={choice.value}>
            {choice.label}
          </option>
        ))}
      </select>
      <button className="btn" disabled={form.processing}>
        Update status
      </button>
      {form.errors.new_status && <div className="error">{form.errors.new_status}</div>}
    </form>
  )
}
