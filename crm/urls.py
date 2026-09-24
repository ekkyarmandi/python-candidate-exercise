from django.urls import path
from . import views
urlpatterns = [path("", views.crm_screen, name="crm"), path("export/", views.export_contacts, name="export_contacts")]
