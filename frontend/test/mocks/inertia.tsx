import type { AnchorHTMLAttributes, ReactNode } from 'react'
import { vi } from 'vitest'

export const router = {
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
  visit: vi.fn(),
}

export const usePage = vi.fn(() => ({ props: { errors: {} } }))
export const useForm = vi.fn()
export const createInertiaApp = vi.fn()

export function Link({
  href,
  children,
  ...rest
}: { href: string; children?: ReactNode } & AnchorHTMLAttributes<HTMLAnchorElement>) {
  return (
    <a href={href} {...rest}>
      {children}
    </a>
  )
}

export function makeForm(overrides: Record<string, unknown> = {}) {
  const form: Record<string, unknown> = {
    data: {},
    setData: vi.fn(),
    transform: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    reset: vi.fn(),
    processing: false,
    errors: {},
    ...overrides,
  }
  ;(form.transform as ReturnType<typeof vi.fn>).mockImplementation(() => form)
  return form
}
