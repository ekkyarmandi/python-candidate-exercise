import type { ReactNode } from 'react'

interface FieldProps {
  id: string
  label: string
  error?: string
  children: ReactNode
}

/**
 * A labelled form control with an optional inline error.
 *
 * The label is associated by id rather than wrapping the control, so the error
 * text is not read as part of the control's name.
 */
export function Field({ id, label, error, children }: FieldProps) {
  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      {children}
      {error ? (
        <p className="field__error" id={`${id}-error`} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}
