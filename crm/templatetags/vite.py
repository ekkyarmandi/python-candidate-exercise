"""Template tag that resolves the Vite build entry from its manifest.

Django owns the HTML shell, so the hashed asset names produced by Vite are
looked up here instead of duplicating them in the template.
"""

import json
from pathlib import Path

from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

ENTRY = "src/main.tsx"
MANIFEST_PATH = Path("crm") / "static" / "crm" / "dist" / ".vite" / "manifest.json"


def _read_manifest():
    path = Path(settings.BASE_DIR) / MANIFEST_PATH
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ImproperlyConfigured(
            "Frontend assets are missing. Run `npm ci && npm run build` in frontend/."
        ) from exc
    except json.JSONDecodeError as exc:
        raise ImproperlyConfigured(f"{path} is not valid JSON. Rebuild the frontend.") from exc


@register.simple_tag
def vite_asset(entry=ENTRY):
    """Render the entry's module script and stylesheet links."""
    manifest = _read_manifest()
    record = manifest.get(entry)
    if not record or "file" not in record:
        raise ImproperlyConfigured(
            f"The Vite manifest has no built entry {entry!r}. Rebuild the frontend."
        )

    tags = [
        format_html('<link rel="stylesheet" href="{}">', static("crm/dist/" + href))
        for href in record.get("css", [])
    ]
    tags.append(
        format_html(
            '<script type="module" src="{}"></script>',
            static("crm/dist/" + record["file"]),
        )
    )
    # Each fragment was produced by format_html, so interpolated values are
    # already escaped; joining drops their SafeString type, which is why the
    # result is marked safe again.
    return mark_safe("\n    ".join(tags))  # nosec
