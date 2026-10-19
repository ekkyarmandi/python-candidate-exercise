import { useCallback, useRef, useState } from 'react'
import { errorMessage, request } from '../lib/api'
import { pickContact } from './payload'
import type {
  Contact,
  Detail,
  InitialData,
  ListPayload,
  StatusChoice,
  Summary,
  UrlState,
} from '../types'

interface Run {
  id: number
  signal: AbortSignal
}

export interface CrmData {
  contacts: Contact[]
  statusChoices: StatusChoice[]
  summary: Summary
  detail: Detail | null
  pending: boolean
  error: string
  loadList: (state: UrlState) => Promise<number | null>
  loadDetail: (contactId: string | number) => Promise<Detail | null>
  applyContact: (contact: Contact, nextSummary?: Summary) => void
  setDetail: (detail: Detail | null) => void
}

/**
 * Owns the screen's server-derived data and the requests that refresh it.
 *
 * Every load aborts the previous one and guards on a request id, so a slow
 * response for an older filter can never overwrite a newer one.
 */
export function useCrmData(initial: InitialData): CrmData {
  const [contacts, setContacts] = useState(initial.contacts)
  const [statusChoices, setStatusChoices] = useState(initial.statusChoices)
  const [summary, setSummary] = useState(initial.summary)
  const [detail, setDetail] = useState(initial.detail)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(initial.serverError)
  const requestId = useRef(0)
  const abortRef = useRef<AbortController | null>(null)

  const begin = useCallback((): Run => {
    requestId.current += 1
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setPending(true)
    setError('')
    return { id: requestId.current, signal: controller.signal }
  }, [])

  const isCurrent = useCallback((id: number): boolean => id === requestId.current, [])

  const loadDetail = useCallback(
    async (contactId: string | number): Promise<Detail | null> => {
      const run = begin()
      try {
        const payload = await request<Detail>(
          '/api/contacts/' + encodeURIComponent(contactId) + '/',
          { signal: run.signal },
        )
        if (!isCurrent(run.id) || !payload) return null
        setDetail(payload)
        return payload
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return null
        if (!isCurrent(run.id)) return null
        setError(errorMessage(err, 'Could not load the contact.'))
        return null
      } finally {
        if (isCurrent(run.id)) setPending(false)
      }
    },
    [begin, isCurrent],
  )

  const loadList = useCallback(
    async (state: UrlState): Promise<number | null> => {
      const run = begin()
      const params = new URLSearchParams()
      if (state.q) params.set('q', state.q)
      if (state.status) params.set('status', state.status)
      try {
        const list = await request<ListPayload>(
          '/api/contacts/?' + params.toString(),
          { signal: run.signal },
        )
        if (!isCurrent(run.id) || !list) return null
        setContacts(list.contacts)
        setSummary(list.summary)
        if (list.status_choices?.length) setStatusChoices(list.status_choices)

        const selected = pickContact(list.contacts, state.contactId)
        if (!selected) {
          setDetail(null)
          return null
        }
        const payload = await request<Detail>('/api/contacts/' + selected.id + '/', {
          signal: run.signal,
        })
        if (!isCurrent(run.id) || !payload) return null
        setDetail(payload)
        return selected.id
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return null
        if (!isCurrent(run.id)) return null
        setError(errorMessage(err, 'Could not load the contact list.'))
        return null
      } finally {
        if (isCurrent(run.id)) setPending(false)
      }
    },
    [begin, isCurrent],
  )

  const applyContact = useCallback(
    (contact: Contact, nextSummary?: Summary): void => {
      setContacts((current) =>
        current.map((row) =>
          row.id === contact.id ? { ...row, ...contact } : row,
        ),
      )
      if (nextSummary) setSummary(nextSummary)
      setDetail((current) =>
        current && current.contact.id === contact.id
          ? { contact, activities: current.activities }
          : current,
      )
    },
    [],
  )

  return {
    contacts,
    statusChoices,
    summary,
    detail,
    pending,
    error,
    loadList,
    loadDetail,
    applyContact,
    setDetail,
  }
}
