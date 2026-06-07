"""
Permissões personalizadas do app core.

Classes:
    EhMembroDoProjeto: usuário deve ser membro (qualquer papel) do projeto.
    EhLiderDoProjeto: usuário deve ter papel 'L' no projeto.
    EhAutorOuLider: usuário é o autor do objeto ou líder do projeto pai.
"""

from rest_framework.permissions import BasePermission

from .models import MembroProjeto


def _papel(user, projeto):
    """
    Retorna o papel ('L' ou 'M') do usuário no projeto, ou None se não for membro.

    Args:
        user (User): Usuário autenticado.
        projeto (Projeto): Projeto alvo.

    Returns:
        str | None: Papel do usuário ou None.
    """
    try:
        return MembroProjeto.objects.get(usuario=user, projeto=projeto).papel
    except MembroProjeto.DoesNotExist:
        return None


class EhMembroDoProjeto(BasePermission):
    """
    Permite acesso somente a membros (Líder ou Membro) do projeto.

    Requer que a view tenha `get_projeto()` ou que o objeto tenha `.projeto`.
    """

    message = "Você não é membro deste projeto."

    def has_object_permission(self, request, view, obj):
        """Verifica se o usuário é membro do projeto do objeto."""
        projeto = getattr(obj, "projeto", obj)
        return _papel(request.user, projeto) is not None


class EhLiderDoProjeto(BasePermission):
    """
    Permite acesso somente a Líderes do projeto.

    Requer que o objeto tenha `.projeto` ou seja o próprio Projeto.
    """

    message = "Apenas o líder pode realizar esta ação."

    def has_object_permission(self, request, view, obj):
        """Verifica se o usuário é líder do projeto do objeto."""
        projeto = getattr(obj, "projeto", obj)
        return _papel(request.user, projeto) == "L"


class EhAutorOuLider(BasePermission):
    """
    Permite edição/exclusão somente ao autor do objeto ou ao líder do projeto.

    Usado em Observacao: o autor edita/exclui a própria; líder exclui qualquer uma.
    """

    message = "Apenas o autor ou o líder do projeto pode realizar esta ação."

    def has_object_permission(self, request, view, obj):
        """Verifica se o usuário é autor do objeto ou líder do projeto pai."""
        # Autor do objeto
        if hasattr(obj, "autor") and obj.autor == request.user:
            return True
        # Líder do projeto pai
        projeto = getattr(obj, "projeto", None)
        if projeto:
            return _papel(request.user, projeto) == "L"
        return False
