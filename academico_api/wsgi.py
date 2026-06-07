"""
Ponto de entrada WSGI para o academico_api_backend.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "academico_api.settings")
application = get_wsgi_application()
