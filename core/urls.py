"""
Rotas da API do app core.

Estrutura de URLs:

    Autenticação:
        POST   /api/auth/registrar/
        POST   /api/auth/login/
        POST   /api/auth/logout/
        GET    /api/auth/perfil/
        PATCH  /api/auth/perfil/

        POST   /api/auth/token/refresh/       (simplejwt refresh)

    Projetos (requer autenticação):
        GET    /api/projetos/
        POST   /api/projetos/
        GET    /api/projetos/{id}/
        PUT    /api/projetos/{id}/
        PATCH  /api/projetos/{id}/
        DELETE /api/projetos/{id}/

    Membros de projeto:
        GET    /api/projetos/{id}/membros/
        DELETE /api/projetos/{id}/membros/{membro_id}/

    Convites por projeto:
        GET    /api/projetos/{id}/convites/
        POST   /api/projetos/{id}/convites/

    Convites do usuário:
        GET    /api/convites/
        POST   /api/convites/{id}/aceitar/
        POST   /api/convites/{id}/recusar/

    Tarefas:
        GET    /api/projetos/{id}/tarefas/
        POST   /api/projetos/{id}/tarefas/
        GET    /api/projetos/{id}/tarefas/{tid}/
        PUT    /api/projetos/{id}/tarefas/{tid}/
        PATCH  /api/projetos/{id}/tarefas/{tid}/
        DELETE /api/projetos/{id}/tarefas/{tid}/

    Observações:
        GET    /api/projetos/{id}/tarefas/{tid}/observacoes/
        POST   /api/projetos/{id}/tarefas/{tid}/observacoes/
        PATCH  /api/projetos/{id}/tarefas/{tid}/observacoes/{oid}/
        DELETE /api/projetos/{id}/tarefas/{tid}/observacoes/{oid}/
"""

from django.urls import path, include
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AuthViewSet,
    ConviteViewSet,
    MembroProjetoViewSet,
    ObservacaoViewSet,
    ProjetoViewSet,
    TarefaViewSet,
)


router = DefaultRouter()
router.register(r"projetos", ProjetoViewSet, basename="projeto")

# Instâncias das views para rotas manuais
auth_view = AuthViewSet.as_view
convite_view = ConviteViewSet.as_view
membro_view = MembroProjetoViewSet.as_view
tarefa_viewset = TarefaViewSet.as_view
obs_viewset = ObservacaoViewSet.as_view

urlpatterns = [

    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Registro e login (públicos)
    path(
        "auth/registrar/",
        auth_view({"post": "registrar"}, permission_classes=[AllowAny]),
        name="auth-registrar",
    ),
    path(
        "auth/login/",
        auth_view({"post": "login"}, permission_classes=[AllowAny]),
        name="auth-login",
    ),
    path(
        "auth/logout/",
        auth_view({"post": "logout"}),
        name="auth-logout",
    ),
    path(
        "auth/perfil/",
        auth_view({"get": "perfil", "patch": "perfil"}),
        name="auth-perfil",
    ),

    # Projetos (via router)
    path("", include(router.urls)),

    # Membros
    path(
        "projetos/<int:projeto_pk>/membros/",
        membro_view({"get": "list"}),
        name="membro-list",
    ),
    path(
        "projetos/<int:projeto_pk>/membros/<int:pk>/",
        membro_view({"delete": "destroy"}),
        name="membro-detail",
    ),

    # Convites por projeto
    path(
        "projetos/<int:projeto_pk>/convites/",
        convite_view({
            "get": "list_for_projeto",
            "post": "create_for_projeto",
        }),
        name="convite-projeto",
    ),

    # Convites do usuário
    path(
        "convites/",
        convite_view({"get": "list"}),
        name="convite-list",
    ),
    path(
        "convites/<int:pk>/aceitar/",
        convite_view({"post": "aceitar"}),
        name="convite-aceitar",
    ),
    path(
        "convites/<int:pk>/recusar/",
        convite_view({"post": "recusar"}),
        name="convite-recusar",
    ),

    # Tarefas
    path(
        "projetos/<int:projeto_pk>/tarefas/",
        tarefa_viewset({
            "get": "list",
            "post": "create",
        }),
        name="tarefa-list",
    ),
    path(
        "projetos/<int:projeto_pk>/tarefas/<int:pk>/",
        tarefa_viewset({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="tarefa-detail",
    ),

    # Observações
    path(
        "projetos/<int:projeto_pk>/tarefas/<int:tarefa_pk>/observacoes/",
        obs_viewset({
            "get": "list",
            "post": "create",
        }),
        name="observacao-list",
    ),
    path(
        "projetos/<int:projeto_pk>/tarefas/<int:tarefa_pk>/observacoes/<int:pk>/",
        obs_viewset({
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="observacao-detail",
    ),
]
