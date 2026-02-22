"""
WSGI config for RepuestoControl EC project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "repuestocontrol.settings")
application = get_wsgi_application()
