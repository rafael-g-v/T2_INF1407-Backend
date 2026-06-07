"""
Ponto de entrada ASGI para o academico_api_backend.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "academico_api.settings")
application = get_asgi_application()
