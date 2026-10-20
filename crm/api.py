"""JSON serialization and API views for the CRM screen.

The serializers are shared by the server-rendered dashboard payloads and the
``/api/`` endpoints so the React client sees one shape regardless of whether
data arrived with the first page load or from a later request.

The endpoints return JSON for every failure mode, including unknown contacts and
rejected CSRF tokens, so the client never has to parse an HTML error page.
"""

import json

from django.http import HttpResponse, JsonResponse
from django.views.csrf import csrf_failure as default_csrf_failure
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import commands
from .models import Contact
from .selectors import get_contacts, get_dashboard_summary


def contact_to_dict(contact):
    """Serialize a contact's display fields."""
    return {
        "id": contact.id,
        "name": contact.name,
        "email": contact.email,
        "company": contact.company,
        "phone": contact.phone,
        "status": contact.status,
        "status_label": contact.get_status_display(),
        "owner": contact.owner,
        "value": float(contact.value),
    }


def activity_to_dict(activity):
    """Serialize an activity, keeping the legacy formatted timestamp."""
    return {
        "kind": activity.kind,
        "body": activity.body,
        "created_by": activity.created_by,
        "created_at": activity.created_at.strftime("%d %b %Y %H:%M"),
        "created_at_iso": activity.created_at.isoformat(),
    }


def summary_to_dict(summary):
    """Serialize the dashboard aggregates for JSON consumers."""
    return {
        "total": summary["total"],
        "pipeline": float(summary["pipeline"] or 0),
        "status_counts": summary["status_counts"],
    }


def contact_detail_to_dict(contact):
    """Serialize a contact with its 20 most recent activities."""
    return {
        "contact": contact_to_dict(contact),
        "activities": [activity_to_dict(activity) for activity in contact.activities.all()[:20]],
    }


def error_response(message, *, status, errors=None):
    """Return a JSON error body, optionally including per-field messages."""
    body = {"error": message}
    if errors:
        body["errors"] = errors
    return JsonResponse(body, status=status)


def find_contact(contact_id):
    """Resolve a URL id to a contact, returning None for bad or missing ids."""
    try:
        pk = int(contact_id)
    except TypeError, ValueError:
        return None
    return Contact.objects.filter(pk=pk).first()


def contact_list_payload(query="", status=""):
    """Return the list response body used by both GET handlers."""
    contacts = get_contacts(query, status)
    return {
        "contacts": [contact_to_dict(contact) for contact in contacts],
        "summary": summary_to_dict(get_dashboard_summary()),
        # Client-rendered pages (Vite dev) have no embedded choices.
        "status_choices": [list(choice) for choice in Contact.STATUS_CHOICES],
    }


def csrf_failure(request, reason=""):
    """Return JSON for API CSRF failures; keep the stock page elsewhere."""
    if request.path.startswith("/api/"):
        return error_response("CSRF verification failed", status=403)
    return default_csrf_failure(request, reason)


@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    """Issue the CSRF cookie for client-rendered pages (the Vite dev server)."""
    return HttpResponse(status=204)


def parse_json_body(request):
    """Return the decoded JSON object, or None when the body is unusable."""
    try:
        data = json.loads(request.body or b"{}")
    except ValueError, UnicodeDecodeError:
        return None
    return data if isinstance(data, dict) else None


@require_http_methods(["GET", "POST"])
def contacts_collection(request):
    """Return the filtered contact list, or create a contact from JSON."""
    if request.method == "GET":
        return JsonResponse(
            contact_list_payload(
                request.GET.get("q", "").strip(),
                request.GET.get("status", "").strip(),
            )
        )

    data = parse_json_body(request)
    if data is None:
        return error_response("Invalid JSON body", status=400)
    errors, contact = commands.create_contact_command(data)
    if errors:
        return error_response("Validation failed", status=400, errors=errors)
    return JsonResponse(
        {
            "contact": contact_to_dict(contact),
            "summary": summary_to_dict(get_dashboard_summary()),
        },
        status=201,
    )


@require_http_methods(["GET", "DELETE"])
def contact_detail(request, contact_id):
    """Return one contact with its recent activity feed, or delete it."""
    contact = find_contact(contact_id)
    if contact is None:
        return error_response("Contact not found", status=404)
    if request.method == "DELETE":
        commands.delete_contact_command(contact)
        return HttpResponse(status=204)
    return JsonResponse(contact_detail_to_dict(contact))


@require_POST
def contact_status(request, contact_id):
    """Change a contact's status and return the refreshed detail payload."""
    contact = find_contact(contact_id)
    if contact is None:
        return error_response("Contact not found", status=404)
    data = parse_json_body(request)
    if data is None:
        return error_response("Invalid JSON body", status=400)
    errors, contact = commands.change_status_command(contact, data)
    if errors:
        return error_response("Validation failed", status=400, errors=errors)
    payload = contact_detail_to_dict(contact)
    payload["summary"] = summary_to_dict(get_dashboard_summary())
    return JsonResponse(payload)


@require_POST
def contact_notes(request, contact_id):
    """Record a note and return the refreshed detail payload."""
    contact = find_contact(contact_id)
    if contact is None:
        return error_response("Contact not found", status=404)
    data = parse_json_body(request)
    if data is None:
        return error_response("Invalid JSON body", status=400)
    commands.add_note_command(contact, data)
    return JsonResponse(contact_detail_to_dict(contact))
