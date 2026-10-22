import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@inertiajs/react', async () => await import('../mocks/inertia'))

import NewContactForm from '@/components/NewContactForm'
import NoteForm from '@/components/NoteForm'
import StatusForm from '@/components/StatusForm'
import { filters, statusChoices } from '../fixtures'
import { makeForm, useForm } from '../mocks/inertia'

const contactFormData = {
  name: '',
  email: '',
  company: '',
  owner: '',
  phone: '',
  value: '',
  new_status: 'lead',
}

describe('NewContactForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('posts the payload to the create endpoint with the active filters', () => {
    const form = makeForm({ data: contactFormData })
    useForm.mockReturnValue(form)

    const { container } = render(
      <NewContactForm filters={{ q: 'alt', status: 'lead' }} statusChoices={statusChoices} />,
    )
    container.querySelector('form')?.requestSubmit()

    expect(form.transform).toHaveBeenCalled()
    expect(form.post).toHaveBeenCalledWith(
      '/contacts/',
      expect.objectContaining({ preserveScroll: true }),
    )
  })

  it('shows the server error and disables submit while processing', () => {
    useForm.mockReturnValue(
      makeForm({ data: contactFormData, errors: { name: 'Name is required' }, processing: true }),
    )

    render(<NewContactForm filters={filters} statusChoices={statusChoices} />)

    expect(screen.getByText('Name is required')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add' })).toBeDisabled()
  })
})

describe('StatusForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('patches the status endpoint for the selected contact', () => {
    const form = makeForm({ data: { new_status: 'lead' } })
    useForm.mockReturnValue(form)

    const { container } = render(
      <StatusForm
        contactId={7}
        currentStatus="lead"
        filters={filters}
        statusChoices={statusChoices}
      />,
    )
    container.querySelector('form')?.requestSubmit()

    expect(form.patch).toHaveBeenCalledWith(
      '/contacts/7/status/',
      expect.objectContaining({ preserveScroll: true }),
    )
  })

  it('shows a validation error for the status field', () => {
    useForm.mockReturnValue(
      makeForm({
        data: { new_status: 'lead' },
        errors: { new_status: 'Select a valid choice.' },
      }),
    )

    render(
      <StatusForm
        contactId={1}
        currentStatus="lead"
        filters={filters}
        statusChoices={statusChoices}
      />,
    )

    expect(screen.getByText('Select a valid choice.')).toBeInTheDocument()
  })
})

describe('NoteForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('posts the note to the contact notes endpoint', () => {
    const form = makeForm({ data: { note: '' } })
    useForm.mockReturnValue(form)

    const { container } = render(<NoteForm contactId={3} filters={filters} />)
    container.querySelector('form')?.requestSubmit()

    expect(form.post).toHaveBeenCalledWith(
      '/contacts/3/notes/',
      expect.objectContaining({ preserveScroll: true }),
    )
  })
})
