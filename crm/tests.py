import csv
import io
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.html import escape

from .models import Activity, Contact


class CrmScreenTests(TestCase):
    def setUp(self):
        self.contact = Contact.objects.create(
            name="Ekky Example",
            email="ekky@example.com",
            company="Altogether",
            status="lead",
            value=1000,
        )

    def test_dashboard_loads(self):
        r = self.client.get(reverse("crm"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Jellybean CRM")

    def test_search(self):
        Contact.objects.create(name="Someone Else", company="Other")
        r = self.client.get(reverse("crm"), {"q": "Altogether"})
        self.assertContains(r, "Ekky Example")
        self.assertNotContains(r, "Someone Else")

    def test_status_filter(self):
        Contact.objects.create(name="Someone Else", company="Other", status="customer")
        r = self.client.get(reverse("crm"), {"status": "lead"})
        self.assertContains(r, "Ekky Example")
        self.assertNotContains(r, "Someone Else")

    def test_change_status(self):
        self.client.post(
            reverse("crm"),
            {"action": "change_status", "contact_id": self.contact.id, "new_status": "qualified"},
        )
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, "qualified")
        self.assertTrue(
            Activity.objects.filter(contact=self.contact, kind="status").exists()
        )

    def test_change_status_writes_body(self):
        self.client.post(
            reverse("crm"),
            {"action": "change_status", "contact_id": self.contact.id, "new_status": "qualified"},
        )
        activity = Activity.objects.get(contact=self.contact, kind="status")
        self.assertEqual(activity.body, "Status changed from lead to qualified")

    def test_add_note(self):
        self.client.post(
            reverse("crm"),
            {"action": "add_note", "contact_id": self.contact.id, "note": "Called customer"},
        )
        self.assertTrue(
            Activity.objects.filter(contact=self.contact, body="Called customer").exists()
        )

    def test_add_note_kind(self):
        self.client.post(
            reverse("crm"),
            {"action": "add_note", "contact_id": self.contact.id, "note": "Called customer"},
        )
        activity = Activity.objects.get(contact=self.contact, body="Called customer")
        self.assertEqual(activity.kind, "note")

    def test_delete_contact(self):
        self.client.post(
            reverse("crm"),
            {"action": "delete_contact", "contact_id": self.contact.id},
        )
        self.assertFalse(Contact.objects.filter(pk=self.contact.id).exists())


class AddContactRuleTests(TestCase):
    """Pin the current add-contact acceptance rules before refactoring them."""

    def test_blank_name_renders_error(self):
        r = self.client.post(reverse("crm"), {"action": "add_contact", "name": ""})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Name is required")
        self.assertFalse(Contact.objects.exists())

    def test_unparsable_value_becomes_zero(self):
        self.client.post(
            reverse("crm"),
            {"action": "add_contact", "name": "Bad Value", "value": "not-a-number"},
        )
        self.assertEqual(Contact.objects.get(name="Bad Value").value, Decimal("0"))

    def test_unknown_status_is_coerced_to_lead(self):
        self.client.post(
            reverse("crm"),
            {"action": "add_contact", "name": "Unknown Status", "new_status": "bogus"},
        )
        self.assertEqual(Contact.objects.get(name="Unknown Status").status, "lead")

    def test_blank_note_creates_no_activity(self):
        contact = Contact.objects.create(name="No Note")
        self.client.post(
            reverse("crm"),
            {"action": "add_note", "contact_id": contact.id, "note": "   "},
        )
        self.assertFalse(Activity.objects.filter(contact=contact).exists())


class ReturnUrlEncodingTests(TestCase):
    def test_special_characters_round_trip(self):
        query = "a b&c#d é"
        Contact.objects.create(name="Encoded", company=query)
        r = self.client.get(reverse("crm"), {"q": query})
        row = r.context["contacts_json"][0]
        parsed = urlparse(row["url"])
        self.assertEqual(parse_qs(parsed.query)["q"], [query])
        self.assertContains(r, 'data-q="' + escape(query) + '"')


class DashboardTemplateTests(TestCase):
    def test_template_loads_split_assets_and_payload_ids(self):
        Contact.objects.create(name="One")
        r = self.client.get(reverse("crm"))
        self.assertContains(r, "crm/dashboard.css")
        self.assertContains(r, "crm/dashboard.js")
        self.assertContains(r, 'id="contacts-data"')
        self.assertContains(r, 'id="detail-data"')
        self.assertContains(r, 'id="server-data"')


class DashboardQueryCountTests(TestCase):
    def _dashboard_query_count(self):
        with CaptureQueriesContext(connection) as captured:
            r = self.client.get(reverse("crm"))
        self.assertEqual(r.status_code, 200)
        return len(captured)

    def test_home_query_count_is_capped(self):
        Contact.objects.create(name="One")
        with self.assertNumQueries(5):
            self.client.get(reverse("crm"))

    def test_home_query_count_does_not_grow_with_contacts(self):
        Contact.objects.create(name="One")
        base = self._dashboard_query_count()
        for i in range(10):
            Contact.objects.create(name=f"Extra {i}")
        self.assertEqual(self._dashboard_query_count(), base)


class ExportContactsTests(TestCase):
    def test_export_csv_header_and_rows(self):
        Contact.objects.create(name="One", company="A")
        Contact.objects.create(name="Two", company="B")
        r = self.client.get(reverse("export_contacts"))
        self.assertEqual(r.status_code, 200)
        rows = list(csv.reader(io.StringIO(r.content.decode())))
        self.assertEqual(
            rows[0], ["Name", "Email", "Company", "Phone", "Status", "Owner", "Value"]
        )
        self.assertEqual(len(rows) - 1, Contact.objects.count())
