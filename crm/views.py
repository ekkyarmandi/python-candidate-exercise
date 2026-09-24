import csv
from decimal import Decimal, InvalidOperation
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Activity, Contact

def crm_screen(request):
    # Deliberately crowded view: query parsing, commands, validation, business logic,
    # serialisation and presentation preparation all live here.
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
            name = request.POST.get("name", "").strip()
            email = request.POST.get("email", "").strip()
            company = request.POST.get("company", "").strip()
            owner = request.POST.get("owner", "").strip()
            phone = request.POST.get("phone", "").strip()
            raw_value = request.POST.get("value", "0").strip()
            new_status = request.POST.get("new_status", "lead").strip()
            if not name:
                error = "Name is required"
            else:
                try:
                    money = Decimal(raw_value or "0")
                except InvalidOperation:
                    money = Decimal("0")
                if new_status not in dict(Contact.STATUS_CHOICES):
                    new_status = "lead"
                c = Contact.objects.create(name=name, email=email, company=company, owner=owner, phone=phone, value=money, status=new_status)
                Activity.objects.create(contact=c, kind="system", body="Contact created")
                selected_id = str(c.id)
                return redirect(_return_url(q, status, selected_id))
        elif action == "change_status":
            c = get_object_or_404(Contact, pk=request.POST.get("contact_id"))
            old = c.status
            new = request.POST.get("new_status", "")
            if new in dict(Contact.STATUS_CHOICES):
                c.status = new
                c.save()
                Activity.objects.create(contact=c, kind="status", body=f"Status changed from {old} to {new}")
            return redirect(_return_url(q, status, c.id))
        elif action == "add_note":
            c = get_object_or_404(Contact, pk=request.POST.get("contact_id"))
            body = request.POST.get("note", "").strip()
            if body:
                Activity.objects.create(contact=c, body=body, kind="note")
            return redirect(_return_url(q, status, c.id))
        elif action == "delete_contact":
            c = get_object_or_404(Contact, pk=request.POST.get("contact_id"))
            c.delete()
            return redirect(_return_url(q, status, ""))

    contacts = Contact.objects.all().order_by("-updated_at")
    if q:
        contacts = contacts.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(company__icontains=q) | Q(owner__icontains=q))
    if status:
        contacts = contacts.filter(status=status)

    selected = None
    if selected_id:
        try:
            selected = Contact.objects.prefetch_related("activities").get(pk=selected_id)
        except (Contact.DoesNotExist, ValueError):
            selected = None
    if selected is None:
        selected = contacts.first()

    rows = []
    for c in contacts:
        rows.append({"id": c.id, "name": c.name, "email": c.email, "company": c.company, "phone": c.phone, "status": c.status, "status_label": c.get_status_display(), "owner": c.owner, "value": float(c.value), "selected": bool(selected and selected.id == c.id), "url": _return_url(q, status, c.id)})

    detail = None
    if selected:
        detail = {"id": selected.id, "name": selected.name, "email": selected.email, "company": selected.company, "phone": selected.phone, "status": selected.status, "owner": selected.owner, "value": float(selected.value), "activities": [{"kind": a.kind, "body": a.body, "created_by": a.created_by, "created_at": a.created_at.strftime("%d %b %Y %H:%M")} for a in selected.activities.all()[:20]]}

    totals = Contact.objects.aggregate(total=Count("id"), pipeline=Sum("value"))
    status_counts = {key: Contact.objects.filter(status=key).count() for key, label in Contact.STATUS_CHOICES}
    return render(request, "crm/dashboard.html", {"contacts_json": rows, "detail_json": detail, "status_choices": Contact.STATUS_CHOICES, "q": q, "status": status, "error": error, "total": totals["total"] or 0, "pipeline": float(totals["pipeline"] or 0), "status_counts": status_counts})

def _return_url(q, status, contact_id):
    bits = []
    if q: bits.append("q=" + q.replace(" ", "+"))
    if status: bits.append("status=" + status)
    if contact_id: bits.append("contact=" + str(contact_id))
    return reverse("crm") + (("?" + "&".join(bits)) if bits else "")

def export_contacts(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="contacts.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Email", "Company", "Phone", "Status", "Owner", "Value"])
    for c in Contact.objects.all().order_by("name"):
        writer.writerow([c.name, c.email, c.company, c.phone, c.status, c.owner, c.value])
    return response
