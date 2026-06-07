"""
Configuração do Django Admin para os modelos do app core.
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import Convite, MembroProjeto, Observacao, Perfil, Projeto, Tarefa


class PerfilInline(admin.StackedInline):
    """Inline do Perfil dentro da edição do User."""

    model = Perfil
    can_delete = False
    verbose_name_plural = "Perfil Acadêmico"


class MembroProjetoInline(admin.TabularInline):
    """Lista de membros dentro da edição do Projeto."""

    model = MembroProjeto
    extra = 0
    readonly_fields = ["data_entrada"]


class TarefaInline(admin.TabularInline):
    """Lista de tarefas dentro da edição do Projeto."""

    model = Tarefa
    extra = 0
    fields = ["titulo", "status", "responsavel", "prazo"]
    readonly_fields = ["criado_em"]


class CustomUserAdmin(UserAdmin):
    """Estende UserAdmin para incluir o Perfil."""

    inlines = [PerfilInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    """Admin do modelo Projeto."""

    list_display = ["nome", "criado_por", "criado_em", "total_membros", "total_tarefas"]
    list_filter = ["criado_em"]
    search_fields = ["nome", "descricao", "criado_por__username"]
    readonly_fields = ["criado_em", "atualizado_em"]
    inlines = [MembroProjetoInline, TarefaInline]

    @admin.display(description="Membros")
    def total_membros(self, obj):
        """Conta membros do projeto."""
        return obj.membros.count()

    @admin.display(description="Tarefas")
    def total_tarefas(self, obj):
        """Conta tarefas do projeto."""
        return obj.tarefas.count()


@admin.register(MembroProjeto)
class MembroProjetoAdmin(admin.ModelAdmin):
    """Admin do modelo MembroProjeto."""

    list_display = ["usuario", "projeto", "papel", "data_entrada"]
    list_filter = ["papel", "data_entrada"]
    search_fields = ["usuario__username", "projeto__nome"]
    readonly_fields = ["data_entrada"]


@admin.register(Convite)
class ConviteAdmin(admin.ModelAdmin):
    """Admin do modelo Convite."""

    list_display = ["projeto", "convidado_por", "convidado", "status", "data_envio"]
    list_filter = ["status", "data_envio"]
    search_fields = ["projeto__nome", "convidado__username", "convidado_por__username"]
    readonly_fields = ["data_envio", "data_resposta"]


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    """Admin do modelo Tarefa."""

    list_display = ["titulo", "projeto", "responsavel", "status", "prazo", "criado_em"]
    list_filter = ["status", "prazo"]
    search_fields = ["titulo", "projeto__nome", "responsavel__username"]
    readonly_fields = ["criado_em", "atualizado_em"]


@admin.register(Observacao)
class ObservacaoAdmin(admin.ModelAdmin):
    """Admin do modelo Observacao."""

    list_display = ["tarefa", "autor", "criado_em"]
    list_filter = ["criado_em"]
    search_fields = ["texto", "autor__username", "tarefa__titulo"]
    readonly_fields = ["criado_em", "atualizado_em"]
