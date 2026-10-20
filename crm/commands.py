"""Write commands shared by the HTML view and the JSON API.

Each handler validates input with the forms in ``forms.py`` and delegates the
transaction boundary to ``services.py``. Handlers return ``(errors, contact)``
so the caller can decide whether to redirect (HTML) or serialize (JSON) without
duplicating validation rules in two places.

``errors`` maps a field name to its first error message; an empty dict means the
command succeeded. ``contact`` is the created or updated contact, or ``None``
after a successful delete or a failed create.
"""

from . import services
from .forms import ContactCreateForm, NoteForm, StatusChangeForm


def form_errors(form):
    """Return the first message per invalid field, keyed by field name."""
    return {field: messages[0] for field, messages in form.errors.items() if messages}


def create_contact_command(data):
    """Validate and create a contact, mirroring the original screen rules."""
    form = ContactCreateForm(data)
    if not form.is_valid():
        return form_errors(form), None
    contact = services.create_contact(
        name=form.cleaned_data["name"],
        email=form.cleaned_data["email"],
        company=form.cleaned_data["company"],
        owner=form.cleaned_data["owner"],
        phone=form.cleaned_data["phone"],
        value=form.cleaned_data["value"],
        status=form.cleaned_data["new_status"],
    )
    return {}, contact


def change_status_command(contact, data):
    """Validate and apply a status change for an existing contact."""
    form = StatusChangeForm(data)
    if not form.is_valid():
        return form_errors(form), contact
    services.change_status(contact=contact, new_status=form.cleaned_data["new_status"])
    return {}, contact


def add_note_command(contact, data):
    """Validate and record a note for an existing contact."""
    form = NoteForm(data)
    if not form.is_valid():
        return form_errors(form), contact
    services.add_note(contact=contact, body=form.cleaned_data["note"])
    return {}, contact


def delete_contact_command(contact):
    """Delete a contact; the caller resolves the object and handles 404s."""
    services.delete_contact(contact=contact)
    return {}, None
