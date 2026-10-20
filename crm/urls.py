from django.urls import path

from . import api, views

urlpatterns = [
    path("", views.crm_screen, name="crm"),
    path("export/", views.export_contacts, name="export_contacts"),
    path("api/csrf/", api.csrf_token, name="api_csrf"),
    path("api/contacts/", api.contacts_collection, name="api_contacts"),
    path(
        "api/contacts/<str:contact_id>/",
        api.contact_detail,
        name="api_contact_detail",
    ),
    path(
        "api/contacts/<str:contact_id>/status/",
        api.contact_status,
        name="api_contact_status",
    ),
    path(
        "api/contacts/<str:contact_id>/notes/",
        api.contact_notes,
        name="api_contact_notes",
    ),
]
