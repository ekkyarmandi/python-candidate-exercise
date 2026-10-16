import csv
from urllib.parse import urlencode

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ContactCreateForm, NoteForm, StatusChangeForm
from .models import Contact
from .selectors import get_contacts, get_dashboard_summary, get_selected_contact
from .services import add_note, change_status, create_contact, delete_contact


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
        if action == "add_contact":
            form = ContactCreateForm(request.POST)
            if form.is_valid():
                contact = create_contact(
                    name=form.cleaned_data["name"],
                    email=form.cleaned_data["email"],
                    company=form.cleaned_data["company"],
                    owner=form.cleaned_data["owner"],
                    phone=form.cleaned_data["phone"],
                    value=form.cleaned_data["value"],
                    status=form.cleaned_data["new_status"],
                )
                return redirect(_return_url(q, status, contact.id))
            error = form.errors.get("name", ["Name is required"])[0]
        elif action == "change_status":
            contact = get_object_or_404(Contact, pk=request.POST.get("contact_id"))
            form = StatusChangeForm(request.POST)
            if form.is_valid():
                change_status(contact=contact, new_status=form.cleaned_data["new_status"])
            return redirect(_return_url(q, status, contact.id))
        elif action == "add_note":
            contact = get_object_or_404(Contact, pk=request.POST.get("contact_id"))
            form = NoteForm(request.POST)
            if form.is_valid():
                add_note(contact=contact, body=form.cleaned_data["note"])
            return redirect(_return_url(q, status, contact.id))
        elif action == "delete_contact":
            contact = get_object_or_404(Contact, pk=request.POST.get("contact_id"))
            delete_contact(contact=contact)
            return redirect(_return_url(q, status, ""))

    contacts = get_contacts(q, status)
    selected = get_selected_contact(selected_id, contacts)

    rows = []
    for c in contacts:
        rows.append({"id": c.id, "name": c.name, "email": c.email, "company": c.company, "phone": c.phone, "status": c.status, "status_label": c.get_status_display(), "owner": c.owner, "value": float(c.value), "selected": bool(selected and selected.id == c.id), "url": _return_url(q, status, c.id)})

    detail = None
    if selected:
        detail = {"id": selected.id, "name": selected.name, "email": selected.email, "company": selected.company, "phone": selected.phone, "status": selected.status, "owner": selected.owner, "value": float(selected.value), "activities": [{"kind": a.kind, "body": a.body, "created_by": a.created_by, "created_at": a.created_at.strftime("%d %b %Y %H:%M")} for a in selected.activities.all()[:20]]}

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
