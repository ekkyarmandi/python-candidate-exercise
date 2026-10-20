#!/usr/bin/env python
"""Django's command-line utility for administrative tasks.

Defaults to the development settings; override with ``DJANGO_SETTINGS_MODULE``
(for example ``messycrm.settings.test`` before running the test suite).
"""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "messycrm.settings.local")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
