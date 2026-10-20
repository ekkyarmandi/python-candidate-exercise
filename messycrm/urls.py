from django.contrib import admin
from django.urls import include, path

from crm.api import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("", include("crm.urls")),
]
