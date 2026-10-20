"""Tests for the JSON API used by the React screen.

Kept separate from ``crm/tests.py`` on purpose: that module pins the legacy
server-rendered contract and must stay untouched during this change.
"""

import json
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from .models import Activity, Contact


def get_json(client, url, data=None):
    response = client.get(url, data or {})
    return response, json.loads(response.content)


class ContactListApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.alpha = Contact.objects.create(
            name="Alpha Co", email="alpha@example.com", company="Alpha", value=100
        )
        self.beta = Contact.objects.create(
            name="Beta Ltd", company="Beta", status="customer", value=250
        )

    def test_list_returns_contacts_newest_first_with_summary(self):
        response, body = get_json(self.client, reverse("api_contacts"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([c["id"] for c in body["contacts"]], [self.beta.id, self.alpha.id])
        self.assertEqual(body["summary"]["total"], 2)
        self.assertEqual(body["summary"]["pipeline"], 350.0)
        self.assertEqual(
            body["status_choices"],
            [
                ["lead", "Lead"],
                ["qualified", "Qualified"],
                ["customer", "Customer"],
                ["inactive", "Inactive"],
            ],
        )
        self.assertEqual(
            set(body["contacts"][0]),
            {
                "id",
                "name",
                "email",
                "company",
                "phone",
                "status",
                "status_label",
                "owner",
                "value",
            },
        )

    def test_search_matches_name_email_company_and_owner(self):
        Contact.objects.create(name="Other", email="other@example.com", owner="Zoe")
        for query, expected in (
            ("alpha", [self.alpha.id]),
            ("alpha@example.com", [self.alpha.id]),
            ("zeta", []),
        ):
            _, body = get_json(self.client, reverse("api_contacts"), {"q": query})
            self.assertEqual([c["id"] for c in body["contacts"]], expected, query)

    def test_status_filter(self):
        _, body = get_json(self.client, reverse("api_contacts"), {"status": "lead"})
        self.assertEqual([c["id"] for c in body["contacts"]], [self.alpha.id])

    def test_empty_result_is_success(self):
        response, body = get_json(self.client, reverse("api_contacts"), {"q": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["contacts"], [])
        self.assertEqual(body["summary"]["total"], 2)


class ContactDetailApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.contact = Contact.objects.create(name="Detail Co", value=Decimal("42.50"))

    def test_detail_includes_contact_and_activities(self):
        Activity.objects.create(contact=self.contact, body="Called", kind="note")
        response, body = get_json(
            self.client, reverse("api_contact_detail", args=[self.contact.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["contact"]["name"], "Detail Co")
        self.assertEqual(body["contact"]["value"], 42.5)
        self.assertEqual([a["body"] for a in body["activities"]], ["Called"])
        self.assertIn("created_at_iso", body["activities"][0])

    def test_detail_caps_activities_at_twenty_newest_first(self):
        for index in range(25):
            Activity.objects.create(contact=self.contact, body=f"note {index}")
        _, body = get_json(self.client, reverse("api_contact_detail", args=[self.contact.id]))
        self.assertEqual(len(body["activities"]), 20)
        self.assertEqual(body["activities"][0]["body"], "note 24")

    def test_missing_contact_is_json_404(self):
        response = self.client.get(reverse("api_contact_detail", args=[self.contact.id + 999]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content)["error"], "Contact not found")

    def test_non_numeric_id_is_json_404(self):
        response = self.client.get("/api/contacts/not-an-id/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", json.loads(response.content))


class ContactCreateApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def post_json(self, payload):
        return self.client.post(
            reverse("api_contacts"), data=json.dumps(payload), content_type="application/json"
        )

    def test_creates_contact_and_activity(self):
        response = self.post_json(
            {
                "name": "New Co",
                "email": "new@example.com",
                "company": "New",
                "owner": "Sam",
                "phone": "+1",
                "value": "123.45",
                "new_status": "qualified",
            }
        )
        self.assertEqual(response.status_code, 201)
        body = json.loads(response.content)
        contact = Contact.objects.get(pk=body["contact"]["id"])
        self.assertEqual(contact.status, "qualified")
        self.assertEqual(contact.value, Decimal("123.45"))
        self.assertTrue(Activity.objects.filter(contact=contact, body="Contact created").exists())
        self.assertEqual(body["summary"]["total"], 1)

    def test_blank_name_is_rejected(self):
        response = self.post_json({"name": "   "})
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body["errors"], {"name": "Name is required"})
        self.assertFalse(Contact.objects.exists())

    def test_unparsable_value_becomes_zero(self):
        response = self.post_json({"name": "Bad Value", "value": "not-a-number"})
        self.assertEqual(response.status_code, 201)
        contact = Contact.objects.get(name="Bad Value")
        self.assertEqual(contact.value, Decimal("0"))

    def test_unknown_status_is_coerced_to_lead(self):
        self.post_json({"name": "Unknown Status", "new_status": "bogus"})
        self.assertEqual(Contact.objects.get(name="Unknown Status").status, "lead")


class ContactDeleteApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.contact = Contact.objects.create(name="Delete Me")
        Activity.objects.create(contact=self.contact, body="note")

    def test_delete_removes_contact_and_activities(self):
        response = self.client.delete(reverse("api_contact_detail", args=[self.contact.id]))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Contact.objects.filter(pk=self.contact.id).exists())
        self.assertFalse(Activity.objects.filter(contact_id=self.contact.id).exists())

    def test_delete_missing_contact_is_json_404(self):
        response = self.client.delete(reverse("api_contact_detail", args=[self.contact.id + 999]))
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", json.loads(response.content))


class ContactStatusApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.contact = Contact.objects.create(name="Status Co", status="lead")

    def post(self, payload):
        return self.client.post(
            reverse("api_contact_status", args=[self.contact.id]),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_status_change_records_activity_and_summary(self):
        response = self.post({"new_status": "qualified"})
        self.assertEqual(response.status_code, 200)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, "qualified")
        activity = Activity.objects.get(contact=self.contact, kind="status")
        self.assertEqual(activity.body, "Status changed from lead to qualified")
        body = json.loads(response.content)
        self.assertEqual(body["contact"]["status"], "qualified")
        self.assertIn("summary", body)

    def test_unknown_status_is_rejected_without_mutation(self):
        response = self.post({"new_status": "bogus"})
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertIn("new_status", body["errors"])
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, "lead")
        self.assertFalse(Activity.objects.filter(contact=self.contact).exists())

    def test_missing_contact_is_json_404(self):
        response = self.client.post(
            reverse("api_contact_status", args=[self.contact.id + 999]),
            data=json.dumps({"new_status": "lead"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", json.loads(response.content))


class ContactNoteApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.contact = Contact.objects.create(name="Note Co")

    def post(self, payload):
        return self.client.post(
            reverse("api_contact_notes", args=[self.contact.id]),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_note_is_recorded(self):
        response = self.post({"note": "Called customer"})
        self.assertEqual(response.status_code, 200)
        activity = Activity.objects.get(contact=self.contact)
        self.assertEqual(activity.kind, "note")
        self.assertEqual(activity.body, "Called customer")
        body = json.loads(response.content)
        self.assertEqual(body["activities"][0]["body"], "Called customer")

    def test_blank_note_creates_no_activity(self):
        response = self.post({"note": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Activity.objects.filter(contact=self.contact).exists())

    def test_missing_contact_is_json_404(self):
        response = self.client.post(
            reverse("api_contact_notes", args=[self.contact.id + 999]),
            data=json.dumps({"note": "x"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", json.loads(response.content))


class ApiCsrfTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse("api_contacts")
        self.payload = json.dumps({"name": "Csrf Co"})

    def test_missing_token_is_json_403_and_does_not_mutate(self):
        response = self.client.post(self.url, data=self.payload, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", json.loads(response.content))
        self.assertFalse(Contact.objects.exists())


class ApiMalformedJsonTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_rejects_unparsable_body(self):
        response = self.client.post(
            reverse("api_contacts"), data="{not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", json.loads(response.content))
        self.assertFalse(Contact.objects.exists())

    def test_status_rejects_unparsable_body(self):
        contact = Contact.objects.create(name="Unchanged")
        response = self.client.post(
            reverse("api_contact_status", args=[contact.id]),
            data="{not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        contact.refresh_from_db()
        self.assertEqual(contact.status, "lead")
        self.assertFalse(Activity.objects.filter(contact=contact).exists())


class CsrfCookieTests(TestCase):
    def test_dashboard_sets_csrf_cookie(self):
        response = Client().get(reverse("crm"))
        self.assertIn("csrftoken", response.cookies)

    def test_request_with_valid_token_is_accepted(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("crm"))
        token = client.cookies["csrftoken"].value
        response = client.post(
            reverse("api_contacts"),
            data=json.dumps({"name": "Token Co"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Contact.objects.filter(name="Token Co").exists())


class CsrfEndpointTests(TestCase):
    def test_endpoint_sets_cookie(self):
        response = Client().get(reverse("api_csrf"))
        self.assertEqual(response.status_code, 204)
        self.assertIn("csrftoken", response.cookies)

    def test_token_from_endpoint_is_accepted(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("api_csrf"))
        token = client.cookies["csrftoken"].value
        response = client.post(
            reverse("api_contacts"),
            data=json.dumps({"name": "Endpoint Token Co"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Contact.objects.filter(name="Endpoint Token Co").exists())


class CsrfDevOriginTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.get(reverse("api_csrf"))
        self.token = self.client.cookies["csrftoken"].value

    def post(self, origin):
        return self.client.post(
            reverse("api_contacts"),
            data=json.dumps({"name": "Dev Origin Co"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
            HTTP_ORIGIN=origin,
        )

    def test_trusted_dev_origin_is_accepted(self):
        response = self.post("http://localhost:5173")
        self.assertEqual(response.status_code, 201)

    def test_untrusted_origin_is_rejected(self):
        response = self.post("http://evil.example")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Contact.objects.exists())
