# Spec Delta

## Purpose

Defines the CRM screen as a single-page interface: it renders the contact list, selection, detail, and actions without full page reloads, keeps its state in the URL, and is delivered as a built client bundle served by Django.

## ADDED Requirements

### Requirement: Single-page bootstrap from a built client

The system SHALL serve the CRM screen at `/` as a server-rendered shell that embeds the initial payload and mounts a built client bundle, so the first paint shows data and interactions never require a full page reload.

#### Scenario: First load renders data immediately
- **WHEN** a user opens `/`
- **THEN** the page shows the summary, contact list, and selected contact from the server-provided payload without waiting for an additional data request

#### Scenario: Client assets come from the application
- **WHEN** the shell loads its client assets
- **THEN** the scripts and styles are served from the application's own origin with no third-party CDN requests

#### Scenario: Client bundle unavailable
- **WHEN** the browser cannot load the built client bundle
- **THEN** the page shows a readable failure message instead of a blank screen

#### Scenario: Boot without an embedded payload
- **WHEN** the client boots on a page that does not provide the embedded payload hooks, such as the Vite dev server
- **THEN** it loads the contact list from the API and shows a loading state before rendering data

### Requirement: Search and status filter without reload

The system SHALL update the contact list when the user searches or changes the status filter, and SHALL keep the interface on the same page rather than performing a full document navigation.

#### Scenario: Search by text
- **WHEN** the user submits a search term
- **THEN** the list shows only matching contacts and the summary reflects the updated page state

#### Scenario: Filter by status
- **WHEN** the user selects a status filter
- **THEN** the list shows only contacts with that status or all contacts when the filter is cleared

#### Scenario: No matches
- **WHEN** the filters match no contacts
- **THEN** the list region shows an explicit empty state and the detail region shows a prompt to select a contact

### Requirement: URL reflects list and selection state

The system SHALL keep the search term, status filter, and selected contact in the URL query string, and SHALL restore that state when the URL is loaded directly or navigated with browser history.

#### Scenario: Deep link to a contact
- **WHEN** a user opens `/?q=acme&status=lead&contact=12`
- **THEN** the search, filter, and contact selection are applied consistently with the URL

#### Scenario: Selection updates the URL
- **WHEN** the user selects a different contact
- **THEN** the URL is updated without a full page load and browser back returns to the previously selected contact

#### Scenario: Invalid or missing selection
- **WHEN** the URL names a contact that does not exist or names no contact
- **THEN** the interface falls back to the first contact in the filtered list, or to no selection when the list is empty, without an error

### Requirement: Contact detail with activity feed

The system SHALL show the selected contact's name, company, email, phone, owner, status, and value, plus its activity entries newest first, capped at the 20 most recent.

#### Scenario: Detail shown for selection
- **WHEN** a contact is selected
- **THEN** the detail region shows all of that contact's core fields and its recent activities

#### Scenario: No selection
- **WHEN** no contact is selected
- **THEN** the detail region shows a prompt to select a contact rather than stale data

### Requirement: Create contact with inline validation

The system SHALL let the user create a contact from the list panel and SHALL show validation feedback next to the offending field without losing the entered values.

#### Scenario: Successful creation
- **WHEN** the user submits a name with optional details
- **THEN** the contact appears in the list, becomes the selection, and the form is cleared

#### Scenario: Blank name rejected
- **WHEN** the user submits an empty name
- **THEN** an inline "Name is required" message is shown, focus moves to the name field, and no contact is created

#### Scenario: Errors announced
- **WHEN** a submission fails validation
- **THEN** the error is announced to assistive technology and the submit control becomes usable again

### Requirement: Status, note, and delete actions

The system SHALL let the user change a contact's status, add a note, and delete the contact from the detail region, and SHALL require an explicit confirmation before deleting.

#### Scenario: Status change
- **WHEN** the user picks a status and confirms the update
- **THEN** the detail shows the new status and the new status activity appears at the top of the feed

#### Scenario: Add note
- **WHEN** the user saves a non-blank note
- **THEN** the note appears at the top of the activity feed and the note field is cleared

#### Scenario: Blank note
- **WHEN** the user submits an empty note
- **THEN** nothing is recorded and the interface indicates that a note is required

#### Scenario: Delete requires confirmation
- **WHEN** the user requests deletion
- **THEN** the contact is only removed after the user confirms in a prompt or dialog

#### Scenario: Delete result
- **WHEN** deletion succeeds
- **THEN** the contact leaves the list and the interface selects the next available contact or shows the no-selection prompt

### Requirement: Summary and CSV export stay available

The system SHALL show the total contact count and total pipeline value, and SHALL keep the CSV export reachable via a plain link that downloads the same export as before.

#### Scenario: Summary reflects data
- **WHEN** the screen loads or the contact data changes
- **THEN** the displayed total and pipeline value reflect the current contact data with locale-formatted numbers

#### Scenario: Export link
- **WHEN** the user activates the export control
- **THEN** the browser downloads the CSV from `/export/` with the existing header and rows

### Requirement: Accessible and responsive interaction

The system SHALL provide labelled controls, keyboard-operable actions and contact selection, visible focus indicators, semantic landmarks and headings, and layouts that remain usable at narrow viewport widths.

#### Scenario: Keyboard operation
- **WHEN** a keyboard-only user tabs through the screen
- **THEN** every filter, form control, contact selection, and action is reachable and operable, with a visible focus indicator

#### Scenario: Contact list semantics
- **WHEN** assistive technology reads the contact list
- **THEN** contacts are exposed as links or buttons with an accessible name that includes the contact name, not as unnamed clickable containers

#### Scenario: Narrow viewport
- **WHEN** the screen is viewed at a mobile-width viewport
- **THEN** the list and detail regions stack and remain scrollable without horizontal page overflow

#### Scenario: Reduced motion
- **WHEN** the user prefers reduced motion
- **THEN** any animation or transition is removed or reduced
