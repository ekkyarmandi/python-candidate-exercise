import { useForm } from '@inertiajs/react'
import type { FormEvent } from 'react'

import type { DashboardFilters, StatusChoice } from '@/types'

interface NewContactFormProps {
  filters: DashboardFilters
  statusChoices: StatusChoice[]
}

export default function NewContactForm({ filters, statusChoices }: NewContactFormProps) {
  const form = useForm({
    name: '',
    email: '',
    company: '',
    owner: '',
    phone: '',
    value: '',
    new_status: 'lead',
  })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    form.transform((data) => ({ ...data, q: filters.q, status: filters.status }))
    form.post('/contacts/', {
      preserveScroll: true,
      onSuccess: () => form.reset(),
    })
  }

  return (
    <div className="newbox">
      <b>Add contact</b>
      <form onSubmit={submit}>
        <input
          name="name"
          placeholder="Name"
          value={form.data.name}
          onChange={(event) => form.setData('name', event.target.value)}
        />
        <input
          name="email"
          placeholder="Email"
          value={form.data.email}
          onChange={(event) => form.setData('email', event.target.value)}
        />
        <input
          name="company"
          placeholder="Company"
          value={form.data.company}
          onChange={(event) => form.setData('company', event.target.value)}
        />
        <input
          name="owner"
          placeholder="Owner"
          value={form.data.owner}
          onChange={(event) => form.setData('owner', event.target.value)}
        />
        <input
          name="phone"
          placeholder="Phone"
          value={form.data.phone}
          onChange={(event) => form.setData('phone', event.target.value)}
        />
        <input
          name="value"
          placeholder="Value"
          value={form.data.value}
          onChange={(event) => form.setData('value', event.target.value)}
        />
        <select
          name="new_status"
          value={form.data.new_status}
          onChange={(event) => form.setData('new_status', event.target.value)}
        >
          {statusChoices.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
        <button className="btn" disabled={form.processing}>
          Add
        </button>
      </form>
      {form.errors.name && <div className="error">{form.errors.name}</div>}
    </div>
  )
}
