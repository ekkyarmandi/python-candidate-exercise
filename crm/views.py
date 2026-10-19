import csv
from urllib.parse import urlencode

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from . import commands
from .api import activity_to_dict, contact_to_dict
from .models import Contact
from .selectors import get_contacts, get_dashboard_summary, get_selected_contact


@ensure_csrf_cookie
def crm_screen(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    selected_id = request.GET.get("contact", "").strip()
    error = ""

    if request.method == "POST":
        action = request.POST.get("action", "")
        q = request.POST.get("return_q", "").strip()
        status = request.POST.get("return_status", "").strip()
        selected_id = request.POST.get("contact_id", "").strip()
        # Compatibility shim: the React app uses /api/, but the original
        # form-encoded actions stay accepted so existing clients keep working.
        if action == "add_contact":
            errors, contact = commands.create_contact_command(request.POST)
            if contact is not None:
                return redirect(_return_url(q, status, contact.id))
            error = errors.get("name", "Name is required")
        elif action == "change_status":
            contact = get_object_or_404(Contact, pk=request.POST.get("contact_id"))
            commands.change_status_command(contact, request.POST)
            return redirect(_return_url(q, status, contact.id))
        elif action == "add_note":
            contact = get_object_or_404(Contact, pk=request.POST.get("contact_id"))
            commands.add_note_command(contact, request.POST)
            return redirect(_return_url(q, status, contact.id))
        elif action == "delete_contact":
            contact = get_object_or_404(Contact, pk=request.POST.get("contact_id"))
            commands.delete_contact_command(contact)
            return redirect(_return_url(q, status, ""))

    contacts = get_contacts(q, status)
    selected = get_selected_contact(selected_id, contacts)

    rows = []
    for c in contacts:
        row = contact_to_dict(c)
        row["selected"] = bool(selected and selected.id == c.id)
        row["url"] = _return_url(q, status, c.id)
        rows.append(row)

    detail = None
    if selected:
        detail = contact_to_dict(selected)
        detail["activities"] = [
            activity_to_dict(activity) for activity in selected.activities.all()[:20]
        ]

    summary = get_dashboard_summary()
    return render(request, "crm/dashboard.html", {"contacts_json": rows, "detail_json": detail, "status_choices": Contact.STATUS_CHOICES, "q": q, "status": status, "error": error, "total": summary["total"], "pipeline": float(summary["pipeline"] or 0), "status_counts": summary["status_counts"]})


def _return_url(q, status, contact_id):
    params = {}
    if q: params["q"] = q
    if status: params["status"] = status
    if contact_id: params["contact"] = str(contact_id)
    query = urlencode(params)
    return reverse("crm") + (("?" + query) if query else "")


def export_contacts(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="contacts.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Email", "Company", "Phone", "Status", "Owner", "Value"])
    for c in Contact.objects.all().order_by("name"):
        writer.writerow([c.name, c.email, c.company, c.phone, c.status, c.owner, c.value])
    return response
