import { useForm } from '@inertiajs/react'
import type { FormEvent } from 'react'

import type { DashboardFilters } from '../types'

interface NoteFormProps {
  contactId: number
  filters: DashboardFilters
}

export default function NoteForm({ contactId, filters }: NoteFormProps) {
  const form = useForm({ note: '' })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    form.transform((data) => ({ ...data, q: filters.q, status: filters.status }))
    form.post(`/contacts/${contactId}/notes/`, {
      preserveScroll: true,
      onSuccess: () => form.reset(),
    })
  }

  return (
    <form onSubmit={submit}>
      <textarea
        name="note"
        placeholder="Add a note"
        value={form.data.note}
        onChange={(event) => form.setData('note', event.target.value)}
      />
      <button className="btn" disabled={form.processing}>
        Save note
      </button>
    </form>
  )
}
