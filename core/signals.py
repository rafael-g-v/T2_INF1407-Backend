"""
Signals do app core.

  - post_save em Projeto → cria automaticamente MembroProjeto com papel 'L'
    para o usuário que criou o projeto.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Projeto, MembroProjeto


@receiver(post_save, sender=Projeto)
def adicionar_criador_como_lider(sender, instance, created, **kwargs):
    """
    Após criar um Projeto, insere o criador como Líder automaticamente.

    Args:
        sender: Classe Projeto.
        instance (Projeto): Instância recém-criada.
        created (bool): True apenas na criação.
    """
    if created:
        MembroProjeto.objects.get_or_create(
            usuario=instance.criado_por,
            projeto=instance,
            defaults={"papel": "L"},
        )
