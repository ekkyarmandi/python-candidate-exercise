import { useEffect, useState } from 'react'
import type { MouseEvent } from 'react'
import { ContactsPanel } from './components/ContactsPanel'
import { DetailPanel } from './components/DetailPanel'
import { Stats } from './components/Stats'
import { Toolbar } from './components/Toolbar'
import { useCrmData } from './data/useCrmData'
import { request } from './lib/api'
import { buildUrl, readUrlState } from './lib/url'
import type {
  CreatePayload,
  Detail,
  InitialData,
  StatusPayload,
  UrlState,
} from './types'

interface AppProps {
  initial: InitialData
  initialUrl: UrlState
}

export function App({ initial, initialUrl }: AppProps) {
  const crm = useCrmData(initial)
  const [url, setUrl] = useState(initialUrl)
  const [notice, setNotice] = useState('')
  const loadList = crm.loadList

  useEffect(() => {
    function handlePopState() {
      const next = readUrlState()
      setUrl(next)
      void loadList(next).then((selectedId) =>
        settleSelection(next, selectedId),
      )
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [loadList])

  // The Vite dev page has no embedded payload, so load once when it is absent.
  useEffect(() => {
    if (initial.hasEmbeddedPayload) {
      settleSelection(initialUrl, initial.detail?.contact.id ?? null)
      return
    }
    void loadList(initialUrl).then((selectedId) =>
      settleSelection(initialUrl, selectedId),
    )
  }, [initial.hasEmbeddedPayload, initial.detail, initialUrl, loadList])

  function navigate(next: UrlState, options: { replace?: boolean } = {}) {
    const target = buildUrl(next)
    if (options.replace) {
      window.history.replaceState(null, '', target)
    } else {
      window.history.pushState(null, '', target)
    }
    setUrl(next)
  }

  function settleSelection(next: UrlState, selectedId: number | null) {
    if (!selectedId) return
    const fixed: UrlState = { ...next, contactId: String(selectedId) }
    if (fixed.contactId === next.contactId) return

    // A slow boot/fetch must not rewrite a URL the user has already changed
    // (for example by submitting a filter while the first load was in flight).
    const current = readUrlState()
    if (
      current.q !== next.q ||
      current.status !== next.status ||
      current.contactId !== next.contactId
    ) {
      return
    }
    navigate(fixed, { replace: true })
  }

  function handleFilterSubmit(values: { q: string; status: string }) {
    const next: UrlState = { ...url, q: values.q, status: values.status }
    navigate(next)
    void loadList(next).then((selectedId) => settleSelection(next, selectedId))
  }

  function handleSelect(
    contactId: number,
    event: MouseEvent<HTMLAnchorElement>,
  ) {
    if (
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey ||
      event.button !== 0
    ) {
      return
    }
    event.preventDefault()
    const next: UrlState = { ...url, contactId: String(contactId) }
    navigate(next)
    if (!crm.detail || crm.detail.contact.id !== contactId) {
      void crm.loadDetail(contactId)
    }
  }

  async function handleCreate(values: Record<string, string>): Promise<void> {
    const result = await request<CreatePayload>('/api/contacts/', {
      method: 'POST',
      body: values,
    })
    if (!result) throw new Error('The server did not return the new contact.')

    const next: UrlState = { ...url, contactId: String(result.contact.id) }
    navigate(next)
    setNotice('Contact created.')
    await loadList(next)
    // Active filters may exclude the new contact, but it should still be the
    // selection (the legacy screen fetched it by id regardless of filters).
    if (next.q || next.status) {
      const created = await request<Detail>(
        '/api/contacts/' + result.contact.id + '/',
      )
      if (created) crm.setDetail(created)
    }
    settleSelection(next, result.contact.id)
  }

  async function handleStatusChange(newStatus: string): Promise<void> {
    const current = crm.detail
    if (!current) return

    const result = await request<StatusPayload>(
      '/api/contacts/' + current.contact.id + '/status/',
      { method: 'POST', body: { new_status: newStatus } },
    )
    if (!result) throw new Error('The server did not return the updated contact.')

    crm.applyContact(result.contact, result.summary)
    crm.setDetail({ contact: result.contact, activities: result.activities })
    setNotice('Status updated to ' + result.contact.status_label + '.')

    if (url.status && url.status !== result.contact.status) {
      const selectedId = await loadList(url)
      settleSelection(url, selectedId)
    }
  }

  async function handleAddNote(note: string): Promise<void> {
    const current = crm.detail
    if (!current) return

    const result = await request<Detail>(
      '/api/contacts/' + current.contact.id + '/notes/',
      { method: 'POST', body: { note } },
    )
    if (!result) throw new Error('The server did not return the note.')

    crm.setDetail(result)
    setNotice('Note saved.')
  }

  async function handleDelete(): Promise<void> {
    const current = crm.detail
    if (!current) return

    await request('/api/contacts/' + current.contact.id + '/', {
      method: 'DELETE',
    })
    const next: UrlState = { ...url, contactId: '' }
    navigate(next)
    setNotice('Contact deleted.')
    const selectedId = await loadList(next)
    settleSelection(next, selectedId)
  }

  return (
    <>
      <a className="skip-link" href="#crm-main">
        Skip to contacts
      </a>
      <header className="top">
        <h1>Jellybean CRM</h1>
      </header>
      <main id="crm-main" className="wrap">
        <p className="visually-hidden" role="status" aria-live="polite">
          {notice}
        </p>
        {crm.error ? (
          <div className="error" role="alert">
            {crm.error}
          </div>
        ) : null}
        <Stats summary={crm.summary} />
        <Toolbar
          key={url.q + '|' + url.status}
          initialQuery={url.q}
          initialStatus={url.status}
          statusChoices={crm.statusChoices}
          onSubmit={handleFilterSubmit}
          busy={crm.pending}
        />
        <div className="grid">
          <ContactsPanel
            contacts={crm.contacts}
            selectedId={crm.detail ? crm.detail.contact.id : null}
            query={url.q}
            status={url.status}
            busy={crm.pending}
            statusChoices={crm.statusChoices}
            onSelect={handleSelect}
            onCreate={handleCreate}
          />
          <DetailPanel
            detail={crm.detail}
            busy={crm.pending}
            statusChoices={crm.statusChoices}
            onChangeStatus={handleStatusChange}
            onAddNote={handleAddNote}
            onDelete={handleDelete}
          />
        </div>
      </main>
    </>
  )
}
