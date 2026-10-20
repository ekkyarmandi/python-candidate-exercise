import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { App } from './App'
import { initialData } from './data/payload'
import { readUrlState } from './lib/url'

const container = document.getElementById('crm-app')

if (container) {
  createRoot(container).render(
    <StrictMode>
      <App
        initial={initialData()}
        initialUrl={readUrlState()}
      />
    </StrictMode>,
  )
}
