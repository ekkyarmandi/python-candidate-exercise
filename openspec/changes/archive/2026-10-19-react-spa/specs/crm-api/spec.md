# Spec Delta

## Purpose

Exposes the CRM's contacts, status changes, and activity notes over JSON so the single-page interface can read and mutate data without full page reloads, while preserving the existing server-side filtering and validation rules.

## ADDED Requirements

### Requirement: Contact list JSON

The system SHALL return the filtered contact list as JSON from `/api/contacts/`, ordering contacts by most recently updated and applying the same query and status filter semantics as the existing dashboard.

#### Scenario: Unfiltered list
- **WHEN** a client requests `/api/contacts/` with no query parameters
- **THEN** the response is JSON containing every contact, most recently updated first, each with id, name, email, company, phone, status, status label, owner, and value

#### Scenario: Search across name, email, company, and owner
- **WHEN** a client requests `/api/contacts/?q=altog`
- **THEN** only contacts whose name, email, company, or owner contains that text case-insensitively are returned

#### Scenario: Status filter
- **WHEN** a client requests `/api/contacts/?status=lead`
- **THEN** only contacts with the `lead` status are returned

#### Scenario: Status choices included
- **WHEN** a client requests the contact list without the server-rendered shell (for example from the Vite dev server)
- **THEN** the response also carries the known status choices as value and label pairs so the client can populate its filters

#### Scenario: Empty result
- **WHEN** no contact matches the filters
- **THEN** the response is a successful JSON response with an empty contact collection rather than an error

### Requirement: Contact detail JSON

The system SHALL return a single contact with its most recent activity entries from `/api/contacts/<id>/`, and SHALL report a missing contact as not found rather than as an empty success.

#### Scenario: Existing contact
- **WHEN** a client requests `/api/contacts/<id>/` for an existing contact
- **THEN** the response contains that contact's fields plus its up to 20 most recent activities, newest first, each with kind, body, created by, and creation time

#### Scenario: Unknown contact
- **WHEN** a client requests `/api/contacts/<id>/` for an id that does not exist
- **THEN** the response status is 404 with a JSON error message

#### Scenario: Non-numeric id
- **WHEN** a client requests `/api/contacts/not-an-id/`
- **THEN** the response is a 404 rather than an unhandled server error

### Requirement: Contact creation with existing validation rules

The system SHALL accept JSON body posts to `/api/contacts/`, create the contact through the existing write service, and return the created record with status 201.

#### Scenario: Valid contact
- **WHEN** a client posts a name with optional email, company, owner, phone, value, and status
- **THEN** the contact is created, its "Contact created" activity is recorded, and the response is 201 with the new contact's id and fields

#### Scenario: Blank name is rejected
- **WHEN** a client posts a missing or blank name
- **THEN** the response status is 400, the body names `name` as the invalid field, no contact is created, and the message reads "Name is required"

#### Scenario: Unparsable value becomes zero
- **WHEN** a client posts a value that is not a number
- **THEN** the contact is created with a value of 0 instead of being rejected

#### Scenario: Unknown status falls back to lead
- **WHEN** a client posts a status that is not one of the known statuses
- **THEN** the contact is created with status `lead`

### Requirement: Status change over JSON

The system SHALL accept a status change for an existing contact and record the change as an activity using the existing write service.

#### Scenario: Status updated
- **WHEN** a client posts a known new status for an existing contact
- **THEN** the contact's status is saved, a status activity reading "Status changed from <old> to <new>" is recorded, and the response contains the updated contact

#### Scenario: Unknown status rejected
- **WHEN** a client posts a status outside the known statuses
- **THEN** the response status is 400 with a JSON error and the contact's status is unchanged

### Requirement: Notes over JSON

The system SHALL accept a note for an existing contact and record it as a note activity only when the note has non-whitespace content.

#### Scenario: Note recorded
- **WHEN** a client posts a non-blank note for an existing contact
- **THEN** a note activity with that body is recorded and the response contains the updated activity list

#### Scenario: Blank note ignored
- **WHEN** a client posts a note that is empty or only whitespace
- **THEN** the request succeeds without creating any activity

### Requirement: Contact deletion over JSON

The system SHALL delete an existing contact and its activities when the client confirms deletion, and SHALL report an already-missing contact as not found.

#### Scenario: Existing contact deleted
- **WHEN** a client sends a delete request for an existing contact
- **THEN** the contact and its activities are removed and the response succeeds without a body

#### Scenario: Missing contact
- **WHEN** a client sends a delete request for a contact that does not exist
- **THEN** the response status is 404 with a JSON error message

### Requirement: CSRF protection and safe errors

The system SHALL reject state-changing JSON requests that lack a valid CSRF token and SHALL return JSON errors, never HTML error pages, for API failures.

#### Scenario: Missing CSRF token
- **WHEN** a state-changing request is sent without a valid CSRF token
- **THEN** the request is rejected with status 403 and the client is not able to mutate data

#### Scenario: Malformed JSON body
- **WHEN** a request body is not valid JSON
- **THEN** the response status is 400 with a JSON error and no data is mutated

### Requirement: CSRF token endpoint

The system SHALL expose a CSRF token endpoint that sets the token cookie, so a client-rendered page served without the Django shell can obtain a token before its first state-changing request.

#### Scenario: Token issued
- **WHEN** a client requests the CSRF token endpoint
- **THEN** the response status is 204 and it sets the CSRF cookie

#### Scenario: Issued token is accepted
- **WHEN** a state-changing request carries the token from that cookie
- **THEN** the request is accepted and the mutation is applied

### Requirement: Legacy form posts remain accepted

The system SHALL continue to accept the existing form-encoded `action` posts on `/` so current clients and the existing test suite keep working while the single-page interface moves to the JSON endpoints.

#### Scenario: Existing form actions still work
- **WHEN** a client posts to `/` with `action` set to `add_contact`, `change_status`, `add_note`, or `delete_contact` and the matching fields
- **THEN** the request performs the same mutation as before and redirects to the dashboard URL with the query, status, and selection preserved

#### Scenario: Blank name error still appears on the page
- **WHEN** a client posts `add_contact` to `/` with a blank name
- **THEN** the page responds successfully and shows the "Name is required" error
