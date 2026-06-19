"""
Views da API de gerenciamento de projetos acadêmicos.
"""

from django.contrib.auth.models import User
from django.utils import timezone

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Convite, MembroProjeto, Observacao, Projeto, Tarefa
from .permissions import EhAutorOuLider, EhLiderDoProjeto, EhMembroDoProjeto
from .serializers import (
    ChangePasswordSerializer,
    ConviteCreateSerializer,
    ConviteSerializer,
    MembroProjetoSerializer,
    ObservacaoCreateUpdateSerializer,
    ObservacaoSerializer,
    PerfilSerializer,
    PerfilUpdateSerializer,
    ProjetoCreateUpdateSerializer,
    ProjetoSerializer,
    RegistroSerializer,
    TarefaCreateUpdateSerializer,
    TarefaSerializer,
)


def _get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


def _is_lider(user, projeto):
    return MembroProjeto.objects.filter(
        usuario=user, projeto=projeto, papel="L"
    ).exists()


def _is_membro(user, projeto):
    return MembroProjeto.objects.filter(usuario=user, projeto=projeto).exists()


@extend_schema(tags=["Autenticação"])
class AuthViewSet(viewsets.ViewSet):
    """Endpoints de autenticação e gerenciamento de conta."""

    @extend_schema(
        summary="Registrar novo usuário",
        request=RegistroSerializer,
        responses={201: {"description": "Usuário criado com sucesso e tokens retornados."}},
    )
    def registrar(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"mensagem": "Usuário criado com sucesso.", "tokens": _get_tokens(user)},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Login",
        request={"application/json": {"type": "object", "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"},
        }, "required": ["username", "password"]}},
        responses={200: {"description": "Tokens JWT retornados."}, 401: {"description": "Credenciais inválidas."}},
    )
    def login(self, request):
        from django.contrib.auth import authenticate

        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"erro": "Username ou senha incorretos."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(_get_tokens(user))

    @extend_schema(
        summary="Logout (invalida o refresh token)",
        request={"application/json": {"type": "object", "properties": {
            "refresh": {"type": "string"},
        }, "required": ["refresh"]}},
        responses={200: {"description": "Token invalidado com sucesso."}},
    )
    def logout(self, request):
        try:
            token = RefreshToken(request.data.get("refresh"))
            token.blacklist()
            return Response({"mensagem": "Logout realizado com sucesso."})
        except Exception:
            return Response(
                {"erro": "Token inválido ou já expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Obter / atualizar perfil do usuário autenticado",
        responses={200: PerfilSerializer},
    )
    def perfil(self, request):
        perfil = request.user.perfil
        if request.method == "PATCH":
            serializer = PerfilUpdateSerializer(
                perfil, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(PerfilSerializer(perfil, context={"request": request}).data)

    @extend_schema(
        summary="Trocar senha do usuário autenticado",
        request=ChangePasswordSerializer,
        responses={
            200: {"description": "Senha alterada com sucesso. Novos tokens JWT retornados."},
            400: {"description": "Senha atual incorreta ou nova senha inválida."},
        },
    )
    def trocar_senha(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data["senha_atual"]):
            return Response(
                {"erro": "Senha atual incorreta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["nova_senha"])
        user.save()

        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                RefreshToken(refresh_token).blacklist()
        except Exception:
            pass

        return Response(
            {
                "mensagem": "Senha alterada com sucesso.",
                "tokens": _get_tokens(user),
            }
        )


@extend_schema(tags=["Projetos"])
@extend_schema_view(
    list=extend_schema(summary="Listar projetos do usuário autenticado"),
    create=extend_schema(summary="Criar novo projeto"),
    retrieve=extend_schema(summary="Detalhar projeto"),
    update=extend_schema(summary="Atualizar projeto completo (apenas líder)"),
    partial_update=extend_schema(summary="Atualizar projeto parcialmente (apenas líder)"),
    destroy=extend_schema(summary="Excluir projeto (apenas líder)"),
)
class ProjetoViewSet(viewsets.ModelViewSet):
    """CRUD completo de Projetos."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProjetoCreateUpdateSerializer
        return ProjetoSerializer

    def get_queryset(self):
        return (
            Projeto.objects.filter(membros__usuario=self.request.user)
            .distinct()
            .prefetch_related("membros", "tarefas")
            .select_related("criado_por__perfil")
        )

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    def update(self, request, *args, **kwargs):
        projeto = self.get_object()
        if not _is_lider(request.user, projeto):
            return Response(
                {"erro": "Apenas o líder pode editar o projeto."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        projeto = self.get_object()
        if not _is_lider(request.user, projeto):
            return Response(
                {"erro": "Apenas o líder pode excluir o projeto."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


@extend_schema(tags=["Membros"])
class MembroProjetoViewSet(viewsets.ViewSet):
    """Gerenciamento de membros de um projeto."""

    permission_classes = [IsAuthenticated]

    def _get_projeto(self, projeto_pk):
        from django.shortcuts import get_object_or_404
        projeto = get_object_or_404(Projeto, pk=projeto_pk)
        if not _is_membro(self.request.user, projeto):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Você não é membro deste projeto.")
        return projeto

    @extend_schema(
        summary="Listar membros do projeto",
        responses={200: MembroProjetoSerializer(many=True)},
    )
    def list(self, request, projeto_pk=None):
        projeto = self._get_projeto(projeto_pk)
        membros = MembroProjeto.objects.filter(projeto=projeto).select_related(
            "usuario__perfil"
        )
        return Response(MembroProjetoSerializer(membros, many=True).data)

    @extend_schema(
        summary="Remover membro do projeto (apenas líder)",
        responses={204: None},
    )
    def destroy(self, request, pk=None, projeto_pk=None):
        from django.shortcuts import get_object_or_404
        projeto = self._get_projeto(projeto_pk)
        if not _is_lider(request.user, projeto):
            return Response(
                {"erro": "Apenas o líder pode remover membros."},
                status=status.HTTP_403_FORBIDDEN,
            )
        membro = get_object_or_404(MembroProjeto, pk=pk, projeto=projeto)
        if membro.papel == "L":
            lideres = MembroProjeto.objects.filter(projeto=projeto, papel="L").count()
            if lideres <= 1:
                return Response(
                    {"erro": "Não é possível remover o único líder do projeto."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        membro.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Convites"])
class ConviteViewSet(viewsets.ViewSet):
    """Gerenciamento de convites de projeto."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar convites recebidos pelo usuário autenticado",
        responses={200: ConviteSerializer(many=True)},
    )
    def list(self, request):
        convites = (
            Convite.objects.filter(convidado=request.user)
            .select_related(
                "projeto__criado_por__perfil",
                "convidado_por__perfil",
                "convidado__perfil",
            )
            .order_by("-data_envio")
        )
        return Response(ConviteSerializer(convites, many=True).data)

    @extend_schema(
        summary="Enviar convite para um usuário (apenas líder)",
        request=ConviteCreateSerializer,
        responses={201: ConviteSerializer},
    )
    def create_for_projeto(self, request, projeto_pk=None):
        from django.shortcuts import get_object_or_404
        projeto = get_object_or_404(Projeto, pk=projeto_pk)
        if not _is_lider(request.user, projeto):
            return Response(
                {"erro": "Apenas o líder pode enviar convites."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ConviteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        convidado = serializer.validated_data["username_convidado"]

        if _is_membro(convidado, projeto):
            return Response(
                {"erro": "Este usuário já é membro do projeto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        convite, criado = Convite.objects.get_or_create(
            projeto=projeto,
            convidado=convidado,
            defaults={"convidado_por": request.user},
        )
        if not criado:
            if convite.status == "A":
                return Response(
                    {"erro": "Este usuário já aceitou um convite para este projeto."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            convite.status = "P"
            convite.convidado_por = request.user
            convite.data_resposta = None
            convite.save()

        return Response(
            ConviteSerializer(convite).data,
            status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Listar convites enviados para um projeto (apenas líder/membro)",
        responses={200: ConviteSerializer(many=True)},
    )
    def list_for_projeto(self, request, projeto_pk=None):
        from django.shortcuts import get_object_or_404
        projeto = get_object_or_404(Projeto, pk=projeto_pk)
        if not _is_membro(request.user, projeto):
            return Response(
                {"erro": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN
            )
        convites = (
            Convite.objects.filter(projeto=projeto)
            .select_related(
                "projeto__criado_por__perfil",
                "convidado_por__perfil",
                "convidado__perfil",
            )
            .order_by("-data_envio")
        )
        return Response(ConviteSerializer(convites, many=True).data)

    @extend_schema(
        summary="Aceitar convite",
        responses={200: {"description": "Convite aceito."}},
    )
    def aceitar(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        convite = get_object_or_404(
            Convite, pk=pk, convidado=request.user, status="P"
        )
        convite.status = "A"
        convite.data_resposta = timezone.now()
        convite.save()
        MembroProjeto.objects.get_or_create(
            usuario=request.user, projeto=convite.projeto, defaults={"papel": "M"}
        )
        return Response({"mensagem": "Convite aceito com sucesso."})

    @extend_schema(
        summary="Recusar convite",
        responses={200: {"description": "Convite recusado."}},
    )
    def recusar(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        convite = get_object_or_404(
            Convite, pk=pk, convidado=request.user, status="P"
        )
        convite.status = "R"
        convite.data_resposta = timezone.now()
        convite.save()
        return Response({"mensagem": "Convite recusado."})


@extend_schema(tags=["Tarefas"])
@extend_schema_view(
    list=extend_schema(summary="Listar tarefas do projeto"),
    create=extend_schema(summary="Criar tarefa no projeto (apenas líder)"),
    retrieve=extend_schema(summary="Detalhar tarefa"),
    update=extend_schema(summary="Atualizar tarefa completa"),
    partial_update=extend_schema(summary="Atualizar tarefa parcialmente"),
    destroy=extend_schema(summary="Excluir tarefa (apenas líder)"),
)
class TarefaViewSet(viewsets.ModelViewSet):
    """CRUD completo de Tarefas de um Projeto."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TarefaCreateUpdateSerializer
        return TarefaSerializer

    def _get_projeto(self):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Projeto, pk=self.kwargs["projeto_pk"])

    def get_queryset(self):
        projeto = self._get_projeto()
        if not _is_membro(self.request.user, projeto):
            return Tarefa.objects.none()
        return (
            Tarefa.objects.filter(projeto=projeto)
            .select_related("responsavel__perfil")
        )

    def create(self, request, *args, **kwargs):
        projeto = self._get_projeto()
        if not _is_lider(request.user, projeto):
            return Response(
                {"erro": "Apenas o líder pode criar tarefas."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = TarefaCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        responsavel = serializer.validated_data.get("responsavel")
        if responsavel and not _is_membro(responsavel, projeto):
            return Response(
                {"erro": "O responsável deve ser membro do projeto."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tarefa = serializer.save(projeto=projeto)
        return Response(
            TarefaSerializer(tarefa, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        projeto = self._get_projeto()
        if not _is_membro(request.user, projeto):
            return Response(
                {"erro": "Você não é membro deste projeto."},
                status=status.HTTP_403_FORBIDDEN,
            )

        campos_lider = {"titulo", "descricao", "prazo"}
        if not _is_lider(request.user, projeto) and (
            campos_lider & set(request.data.keys())
        ):
            return Response(
                {"erro": "Apenas o líder pode alterar título, descrição e prazo."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Captura o status atual antes de salvar para detectar mudança
        tarefa_antes = self.get_object()
        status_antes = tarefa_antes.status

        resposta = super().update(request, *args, **kwargs)

        # Se o status mudou, cria observação automática
        if "status" in request.data:
            novo_status = request.data["status"]
            if novo_status != status_antes:
                status_labels = {
                    "P": "Pendente",
                    "E": "Em andamento",
                    "C": "Concluída",
                }
                papel = "Líder" if _is_lider(request.user, projeto) else "Membro"
                if hasattr(request.user, "perfil"):
                    nome_completo = f"{request.user.perfil.nome} {request.user.perfil.sobrenome}"
                else:
                    nome_completo = request.user.username
                texto_obs = (
                    f'Status alterado de "{status_labels.get(status_antes, status_antes)}" '
                    f'para "{status_labels.get(novo_status, novo_status)}" '
                    f"por {nome_completo} ({papel})."
                )
                tarefa_atualizada = self.get_object()
                Observacao.objects.create(
                    tarefa=tarefa_atualizada,
                    autor=request.user,
                    texto=texto_obs,
                )

        return resposta

    def destroy(self, request, *args, **kwargs):
        projeto = self._get_projeto()
        if not _is_lider(request.user, projeto):
            return Response(
                {"erro": "Apenas o líder pode excluir tarefas."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


@extend_schema(tags=["Observações"])
@extend_schema_view(
    list=extend_schema(summary="Listar observações da tarefa"),
    create=extend_schema(summary="Adicionar observação à tarefa (qualquer membro)"),
    update=extend_schema(summary="Editar observação (autor ou líder)"),
    partial_update=extend_schema(summary="Editar observação parcialmente (autor ou líder)"),
    destroy=extend_schema(summary="Excluir observação (autor ou líder)"),
)
class ObservacaoViewSet(viewsets.ModelViewSet):
    """CRUD completo de Observações de uma Tarefa."""

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return ObservacaoCreateUpdateSerializer
        return ObservacaoSerializer

    def _get_tarefa(self):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(
            Tarefa,
            pk=self.kwargs["tarefa_pk"],
            projeto__membros__usuario=self.request.user,
        )

    def get_queryset(self):
        tarefa = self._get_tarefa()
        return Observacao.objects.filter(tarefa=tarefa).select_related("autor__perfil")

    def create(self, request, *args, **kwargs):
        tarefa = self._get_tarefa()
        serializer = ObservacaoCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obs = serializer.save(tarefa=tarefa, autor=request.user)
        return Response(
            ObservacaoSerializer(obs, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        obs = self.get_object()
        projeto = obs.tarefa.projeto
        eh_autor = obs.autor == request.user
        eh_lider = _is_lider(request.user, projeto)
        if not (eh_autor or eh_lider):
            return Response(
                {"erro": "Apenas o autor ou líder pode editar esta observação."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obs = self.get_object()
        projeto = obs.tarefa.projeto
        eh_autor = obs.autor == request.user
        eh_lider = _is_lider(request.user, projeto)
        if not (eh_autor or eh_lider):
            return Response(
                {"erro": "Apenas o autor ou líder pode excluir esta observação."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)