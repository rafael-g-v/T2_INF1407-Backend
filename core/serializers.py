from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import (
    Convite,
    MembroProjeto,
    Observacao,
    Perfil,
    Projeto,
    Tarefa,
)


class RegistroSerializer(serializers.ModelSerializer):
    """Serializer para criação de novo usuário com perfil acadêmico."""

    nome = serializers.CharField(write_only=True)
    sobrenome = serializers.CharField(write_only=True)
    matricula = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        label="Confirmação de senha",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2", "nome", "sobrenome", "matricula"]

    def validate_matricula(self, value):
        """Verifica se a matrícula já está em uso antes de criar o usuário."""
        if Perfil.objects.filter(matricula=value).exists():
            raise serializers.ValidationError(
                f"A matrícula '{value}' já está cadastrada. Utilize outra matrícula ou faça login com a conta existente."
            )
        return value

    def validate(self, attrs):
        """Valida que as senhas coincidem e atendem às políticas do Django."""
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "As senhas não coincidem."})
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return attrs

    def create(self, validated_data):
        """Cria o User e o Perfil associado em uma transação."""
        nome = validated_data.pop("nome")
        sobrenome = validated_data.pop("sobrenome")
        matricula = validated_data.pop("matricula")
        validated_data.pop("password2")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        Perfil.objects.create(
            usuario=user, nome=nome, sobrenome=sobrenome, matricula=matricula
        )
        return user


class PerfilSerializer(serializers.ModelSerializer):
    """Serializer de leitura/escrita do perfil acadêmico."""

    username = serializers.CharField(source="usuario.username", read_only=True)
    email = serializers.EmailField(source="usuario.email", read_only=True)

    class Meta:
        model = Perfil
        fields = ["username", "email", "nome", "sobrenome", "matricula"]


class PerfilUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de nome, sobrenome e matrícula do perfil."""

    class Meta:
        model = Perfil
        fields = ["nome", "sobrenome", "matricula"]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para troca de senha do usuário autenticado."""

    senha_atual = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        label="Senha atual",
    )
    nova_senha = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        label="Nova senha",
    )
    nova_senha2 = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        label="Confirmar nova senha",
    )

    def validate(self, attrs):
        """Valida que as novas senhas coincidem e atendem às políticas do Django."""
        if attrs["nova_senha"] != attrs["nova_senha2"]:
            raise serializers.ValidationError(
                {"nova_senha2": "As senhas não coincidem."}
            )
        try:
            validate_password(attrs["nova_senha"])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"nova_senha": list(e.messages)})
        return attrs


class UsuarioResumoSerializer(serializers.ModelSerializer):
    """Representação compacta de um usuário para uso em relacionamentos."""

    nome_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "nome_completo"]

    def get_nome_completo(self, obj):
        """Retorna nome completo do perfil, se existir."""
        if hasattr(obj, "perfil"):
            return f"{obj.perfil.nome} {obj.perfil.sobrenome}"
        return obj.get_full_name() or obj.username


class ProjetoSerializer(serializers.ModelSerializer):
    """Serializer completo de Projeto com informações do criador."""

    criado_por = UsuarioResumoSerializer(read_only=True)
    total_membros = serializers.SerializerMethodField()
    total_tarefas = serializers.SerializerMethodField()
    meu_papel = serializers.SerializerMethodField()

    class Meta:
        model = Projeto
        fields = [
            "id",
            "nome",
            "descricao",
            "criado_por",
            "criado_em",
            "atualizado_em",
            "total_membros",
            "total_tarefas",
            "meu_papel",
        ]
        read_only_fields = ["id", "criado_por", "criado_em", "atualizado_em"]

    def get_total_membros(self, obj):
        """Retorna a quantidade de membros do projeto."""
        return obj.membros.count()

    def get_total_tarefas(self, obj):
        """Retorna a quantidade de tarefas do projeto."""
        return obj.tarefas.count()

    def get_meu_papel(self, obj):
        """Retorna o papel do usuário autenticado no projeto."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                membro = MembroProjeto.objects.get(
                    usuario=request.user, projeto=obj
                )
                return membro.get_papel_display()
            except MembroProjeto.DoesNotExist:
                return None
        return None


class ProjetoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de Projeto."""

    class Meta:
        model = Projeto
        fields = ["nome", "descricao"]


class MembroProjetoSerializer(serializers.ModelSerializer):
    """Serializer de listagem de membros de um projeto."""

    usuario = UsuarioResumoSerializer(read_only=True)
    papel_display = serializers.CharField(source="get_papel_display", read_only=True)

    class Meta:
        model = MembroProjeto
        fields = ["id", "usuario", "papel", "papel_display", "data_entrada"]
        read_only_fields = ["id", "data_entrada"]


class ConviteSerializer(serializers.ModelSerializer):
    """Serializer de leitura de Convite."""

    projeto = ProjetoSerializer(read_only=True)
    convidado_por = UsuarioResumoSerializer(read_only=True)
    convidado = UsuarioResumoSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Convite
        fields = [
            "id",
            "projeto",
            "convidado_por",
            "convidado",
            "status",
            "status_display",
            "data_envio",
            "data_resposta",
        ]
        read_only_fields = fields


class ConviteCreateSerializer(serializers.Serializer):
    """Serializer para envio de convite (recebe username do convidado)."""

    username_convidado = serializers.CharField(
        help_text="Username do usuário a ser convidado."
    )

    def validate_username_convidado(self, value):
        """Verifica se o usuário existe."""
        try:
            return User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                f"Usuário '{value}' não encontrado."
            )


class ObservacaoSerializer(serializers.ModelSerializer):
    """Serializer completo de Observacao."""

    autor = UsuarioResumoSerializer(read_only=True)

    class Meta:
        model = Observacao
        fields = ["id", "texto", "autor", "tarefa", "criado_em", "atualizado_em"]
        read_only_fields = ["id", "autor", "tarefa", "criado_em", "atualizado_em"]


class ObservacaoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e edição de Observacao."""

    class Meta:
        model = Observacao
        fields = ["texto"]


class TarefaSerializer(serializers.ModelSerializer):
    """Serializer completo de Tarefa."""

    responsavel = UsuarioResumoSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_observacoes = serializers.SerializerMethodField()

    class Meta:
        model = Tarefa
        fields = [
            "id",
            "titulo",
            "descricao",
            "projeto",
            "responsavel",
            "status",
            "status_display",
            "prazo",
            "criado_em",
            "atualizado_em",
            "total_observacoes",
        ]
        read_only_fields = [
            "id",
            "projeto",
            "criado_em",
            "atualizado_em",
            "total_observacoes",
        ]

    def get_total_observacoes(self, obj):
        """Retorna a quantidade de observações da tarefa."""
        return obj.observacoes.count()


class TarefaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e edição de Tarefa."""

    responsavel_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="responsavel",
        allow_null=True,
        required=False,
        help_text="ID do usuário responsável (deve ser membro do projeto).",
    )

    class Meta:
        model = Tarefa
        fields = ["titulo", "descricao", "responsavel_id", "status", "prazo"]