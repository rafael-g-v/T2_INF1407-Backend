"""
URL raiz do projeto academico_api_backend.

Todas as rotas da API ficam sob o prefixo /api/.
A documentação Swagger está disponível em /api/docs/.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Admin do Django
    path("admin/", admin.site.urls),

    # Rotas da aplicação
    path("api/", include("core.urls")),

    # Schema OpenAPI (JSON)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # ReDoc (alternativa ao Swagger)
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
