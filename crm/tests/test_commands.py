"""Write-side behaviour of the CRM dashboard screen."""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from crm.models import Activity, Contact


class CrmWriteCommandTests(TestCase):
    def setUp(self):
        self.contact = Contact.objects.create(
            name="Ekky Example",
            email="ekky@example.com",
            company="Altogether",
            status="lead",
            value=1000,
        )

    def test_change_status(self):
        self.client.post(
            reverse("crm"),
            {
                "action": "change_status",
                "contact_id": self.contact.id,
                "new_status": "qualified",
            },
        )
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, "qualified")
        self.assertTrue(
            Activity.objects.filter(contact=self.contact, kind="status").exists()
        )

    def test_change_status_writes_body(self):
        self.client.post(
            reverse("crm"),
            {
                "action": "change_status",
                "contact_id": self.contact.id,
                "new_status": "qualified",
            },
        )
        activity = Activity.objects.get(contact=self.contact, kind="status")
        self.assertEqual(activity.body, "Status changed from lead to qualified")

    def test_add_note(self):
        self.client.post(
            reverse("crm"),
            {
                "action": "add_note",
                "contact_id": self.contact.id,
                "note": "Called customer",
            },
        )
        self.assertTrue(
            Activity.objects.filter(
                contact=self.contact, body="Called customer"
            ).exists()
        )

    def test_add_note_kind(self):
        self.client.post(
            reverse("crm"),
            {
                "action": "add_note",
                "contact_id": self.contact.id,
                "note": "Called customer",
            },
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
        response = self.client.post(
            reverse("crm"), {"action": "add_contact", "name": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Name is required")
        self.assertFalse(Contact.objects.exists())

    def test_unparsable_value_becomes_zero(self):
        self.client.post(
            reverse("crm"),
            {"action": "add_contact", "name": "Bad Value", "value": "not-a-number"},
        )
        self.assertEqual(Contact.objects.get(name="Bad Value").value, Decimal(0))

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
