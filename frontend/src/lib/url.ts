import type { UrlState } from '../types'

export function readUrlState(search = window.location.search): UrlState {
  const params = new URLSearchParams(search)
  return {
    q: (params.get('q') ?? '').trim(),
    status: (params.get('status') ?? '').trim(),
    contactId: params.get('contact') ?? '',
  }
}

export function buildUrl(state: {
  q?: string
  status?: string
  contactId?: string
}): string {
  const params = new URLSearchParams()
  if (state.q) params.set('q', state.q)
  if (state.status) params.set('status', state.status)
  if (state.contactId) params.set('contact', state.contactId)
  const query = params.toString()
  return query ? '/?' + query : '/'
}

export function buildRowHref(
  state: { q: string; status: string },
  contactId: number | string,
): string {
  return buildUrl({
    q: state.q,
    status: state.status,
    contactId: String(contactId),
  })
}
