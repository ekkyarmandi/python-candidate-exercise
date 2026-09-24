from django.test import TestCase
from django.urls import reverse
from .models import Activity, Contact
class CrmScreenTests(TestCase):
    def setUp(self):
        self.contact=Contact.objects.create(name="Ekky Example",email="ekky@example.com",company="Altogether",status="lead",value=1000)
    def test_dashboard_loads(self):
        r=self.client.get(reverse("crm")); self.assertEqual(r.status_code,200); self.assertContains(r,"Jellybean CRM")
    def test_search(self):
        Contact.objects.create(name="Someone Else",company="Other")
        r=self.client.get(reverse("crm"),{"q":"Altogether"}); self.assertContains(r,"Ekky Example"); self.assertNotContains(r,"Someone Else")
    def test_change_status(self):
        self.client.post(reverse("crm"),{"action":"change_status","contact_id":self.contact.id,"new_status":"qualified"})
        self.contact.refresh_from_db(); self.assertEqual(self.contact.status,"qualified"); self.assertTrue(Activity.objects.filter(contact=self.contact,kind="status").exists())
    def test_add_note(self):
        self.client.post(reverse("crm"),{"action":"add_note","contact_id":self.contact.id,"note":"Called customer"})
        self.assertTrue(Activity.objects.filter(contact=self.contact,body="Called customer").exists())
