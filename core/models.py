"""
Modelos do sistema de gerenciamento de projetos acadêmicos.

Entidades principais:
    - Perfil: extensão do User com dados acadêmicos.
    - Projeto: projeto acadêmico criado por um usuário.
    - MembroProjeto: associação usuário ↔ projeto (Líder ou Membro).
    - Convite: convite de um líder para outro usuário entrar no projeto.
    - Tarefa: tarefa dentro de um projeto com responsável e prazo.
    - Observacao: comentário de um membro sobre uma tarefa.
"""

from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):
    """
    Extensão 1-para-1 do User padrão do Django com dados acadêmicos.

    Attributes:
        usuario (User): Usuário Django vinculado.
        nome (str): Primeiro nome.
        sobrenome (str): Sobrenome.
        matricula (str): Matrícula acadêmica única no sistema.
    """

    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil"
    )
    nome = models.CharField(max_length=100, verbose_name="Nome")
    sobrenome = models.CharField(max_length=100, verbose_name="Sobrenome")
    matricula = models.CharField(
        max_length=20, unique=True, verbose_name="Matrícula"
    )

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):  # noqa: D105
        return f"{self.nome} {self.sobrenome}"


class Projeto(models.Model):
    """
    Projeto acadêmico criado por um usuário.

    O criador vira Líder automaticamente via signal (ver signals.py).

    Attributes:
        nome (str): Nome do projeto.
        descricao (str): Descrição do projeto.
        criado_por (User): Usuário que criou o projeto.
        criado_em (datetime): Data/hora de criação.
        atualizado_em (datetime): Data/hora da última atualização.
    """

    nome = models.CharField(max_length=200, verbose_name="Nome")
    descricao = models.TextField(verbose_name="Descrição")
    criado_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projetos_criados",
        verbose_name="Criado por",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ["-criado_em"]

    def __str__(self):  # noqa: D105
        return self.nome


class MembroProjeto(models.Model):
    """
    Associação entre usuário e projeto com papel definido.

    Um usuário não pode aparecer duas vezes no mesmo projeto
    (unique_together garante isso).

    Attributes:
        usuario (User): Usuário membro.
        projeto (Projeto): Projeto ao qual pertence.
        papel (str): 'L' Líder | 'M' Membro.
        data_entrada (date): Data de entrada, preenchida automaticamente.
    """

    PAPEL_CHOICES = [
        ("L", "Líder"),
        ("M", "Membro"),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Usuário"
    )
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name="membros",
        verbose_name="Projeto",
    )
    papel = models.CharField(
        max_length=1, choices=PAPEL_CHOICES, default="M", verbose_name="Papel"
    )
    data_entrada = models.DateField(auto_now_add=True, verbose_name="Data de entrada")

    class Meta:
        verbose_name = "Membro do projeto"
        verbose_name_plural = "Membros dos projetos"
        unique_together = ("usuario", "projeto")

    def __str__(self):  # noqa: D105
        return (
            f"{self.usuario.username} – {self.projeto.nome} "
            f"({self.get_papel_display()})"
        )


class Convite(models.Model):
    """
    Convite de um líder para outro usuário entrar em um projeto.

    Um convite recusado pode ser reenviado; o registro é reutilizado
    (status volta para 'P') para evitar duplicatas.

    Attributes:
        projeto (Projeto): Projeto do convite.
        convidado_por (User): Líder que enviou o convite.
        convidado (User): Usuário convidado.
        status (str): 'P' Pendente | 'A' Aceito | 'R' Recusado.
        data_envio (datetime): Timestamp de envio.
        data_resposta (datetime): Timestamp da resposta; nulo enquanto pendente.
    """

    STATUS_CHOICES = [
        ("P", "Pendente"),
        ("A", "Aceito"),
        ("R", "Recusado"),
    ]

    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name="convites",
        verbose_name="Projeto",
    )
    convidado_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="convites_enviados",
        verbose_name="Convidado por",
    )
    convidado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="convites_recebidos",
        verbose_name="Convidado",
    )
    status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default="P", verbose_name="Status"
    )
    data_envio = models.DateTimeField(auto_now_add=True, verbose_name="Data de envio")
    data_resposta = models.DateTimeField(
        null=True, blank=True, verbose_name="Data de resposta"
    )

    class Meta:
        verbose_name = "Convite"
        verbose_name_plural = "Convites"
        unique_together = ("projeto", "convidado")

    def __str__(self):  # noqa: D105
        return (
            f"{self.convidado_por.username} convidou "
            f"{self.convidado.username} para {self.projeto.nome}"
        )


class Tarefa(models.Model):
    """
    Tarefa de um projeto com responsável opcional e prazo.

    Quando o responsável é removido do projeto, o campo vira NULL
    (on_delete=SET_NULL) preservando o histórico da tarefa.

    Attributes:
        titulo (str): Título curto da tarefa.
        descricao (str): Detalhamento da tarefa.
        projeto (Projeto): Projeto ao qual pertence.
        responsavel (User | None): Membro responsável; pode ser nulo.
        status (str): 'P' Pendente | 'E' Em andamento | 'C' Concluída.
        prazo (date | None): Data limite; opcional.
        criado_em (datetime): Timestamp de criação.
        atualizado_em (datetime): Timestamp da última edição.
    """

    STATUS_CHOICES = [
        ("P", "Pendente"),
        ("E", "Em andamento"),
        ("C", "Concluída"),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    descricao = models.TextField(verbose_name="Descrição")
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name="tarefas",
        verbose_name="Projeto",
    )
    responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tarefas",
        verbose_name="Responsável",
    )
    status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default="P", verbose_name="Status"
    )
    prazo = models.DateField(null=True, blank=True, verbose_name="Prazo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"
        ordering = ["prazo", "status"]

    def __str__(self):  # noqa: D105
        return self.titulo


class Observacao(models.Model):
    """
    Comentário de um membro sobre uma tarefa.

    Qualquer membro do projeto pode criar observações.
    O autor pode editar/excluir a própria; o líder pode excluir qualquer uma.

    Attributes:
        texto (str): Conteúdo da observação.
        tarefa (Tarefa): Tarefa comentada.
        autor (User): Usuário autor.
        criado_em (datetime): Timestamp de criação.
        atualizado_em (datetime): Timestamp da última edição.
    """

    texto = models.TextField(verbose_name="Texto")
    tarefa = models.ForeignKey(
        Tarefa,
        on_delete=models.CASCADE,
        related_name="observacoes",
        verbose_name="Tarefa",
    )
    autor = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Autor"
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(
        auto_now=True, verbose_name="Atualizado em"
    )

    class Meta:
        verbose_name = "Observação"
        verbose_name_plural = "Observações"
        ordering = ["criado_em"]

    def __str__(self):  # noqa: D105
        return (
            f"Obs. de {self.autor.username} em "
            f"{self.criado_em.strftime('%d/%m/%Y %H:%M')}"
        )
