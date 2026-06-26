"""
Rotas da API do app core.

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

    # Troca de senha (requer autenticação)
    path(
        "auth/trocar-senha/",
        auth_view({"post": "trocar_senha"}),
        name="auth-trocar-senha",
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