## Índice

- [Descrição do Projeto](#descrição-do-projeto)
- [Instalação Local](#instalação-local)
- [Documentação da API (Swagger)](#documentação-da-api-swagger)
- [Endpoints Principais](#endpoints-principais)
- [Manual do Usuário / Administrador](#manual-do-usuário--administrador)
- [O que funcionou](#o-que-funcionou)
- [O que não funcionou](#o-que-não-funcionou)

---

## Descrição do Projeto

**Acadêmico** é uma API REST para gerenciamento de projetos acadêmicos colaborativos. Estudantes criam projetos, convidam colegas, atribuem tarefas e acompanham o andamento via observações.

### Escopo implementado

- Usuários e perfis: cada conta tem nome, sobrenome, matrícula e e-mail institucional.
- Projetos: criação e edição de projetos com nome e descrição.
- Membros: o criador do projeto vira Líder automaticamente; outros entram como Membros via convite.
- Convites: líderes convidam por username; o convidado pode aceitar ou recusar.
- Tarefas: o líder cria tarefas com responsável, prazo e status (Pendente, Em andamento ou Concluída).
- Observações: qualquer membro pode comentar em tarefas. Mudanças de status geram uma observação automática com o nome de quem fez a alteração.
- Autenticação JWT: tokens de acesso com validade de 1 hora e refresh por 7 dias, com blacklist no logout.
- Swagger e ReDoc: documentação interativa em `/api/docs/` e `/api/redoc/`.
- Admin Django para gerenciamento direto de todos os modelos.

---

## Instalação Local

### Passo a passo

```bash
# 1. Clone o repositório
git clone <URL_DO_REPOSITORIO_BACKEND>
cd backend_clean

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env            # edite o arquivo com os seus valores
# Variáveis mínimas para rodar localmente:
#   SECRET_KEY=qualquer-string-longa
#   DEBUG=True
#   ALLOWED_HOSTS=localhost,127.0.0.1
#   CORS_ALLOW_ALL_ORIGINS=True

# 5. Aplique as migrações
python manage.py migrate

# 6. Crie um superusuário para o Admin
python manage.py createsuperuser

# 7. Inicie o servidor
python manage.py runserver
```

A API fica disponível em **http://localhost:8000/api/**.
O Swagger fica em **http://localhost:8000/api/docs/**.

---

## Documentação da API (Swagger)

| Endereço | Descrição |
|---|---|
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | Schema OpenAPI em JSON |

Para autenticar no Swagger:

1. Faça `POST /api/auth/login/` com seu `username` e `password`.
2. Copie o valor de `access` retornado.
3. Clique em **Authorize** (canto superior direito) e informe `Bearer <access>`.

---

## Endpoints Principais

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| `POST` | `/api/auth/registrar/` | Criar conta | Não |
| `POST` | `/api/auth/login/` | Login, retorna tokens JWT | Não |
| `POST` | `/api/auth/logout/` | Logout, invalida refresh token | Sim |
| `GET / PATCH` | `/api/auth/perfil/` | Ver / editar perfil | Sim |
| `POST` | `/api/auth/trocar-senha/` | Trocar senha | Sim |
| `GET / POST` | `/api/projetos/` | Listar / criar projetos | Sim |
| `GET / PUT / DELETE` | `/api/projetos/{id}/` | Detalhar / editar / excluir | Sim |
| `GET` | `/api/projetos/{id}/membros/` | Listar membros | Sim |
| `DELETE` | `/api/projetos/{id}/membros/{mid}/` | Remover membro (só Líder) | Sim |
| `GET / POST` | `/api/projetos/{id}/convites/` | Listar / enviar convites | Sim |
| `GET` | `/api/convites/` | Meus convites recebidos | Sim |
| `POST` | `/api/convites/{id}/aceitar/` | Aceitar convite | Sim |
| `POST` | `/api/convites/{id}/recusar/` | Recusar convite | Sim |
| `GET / POST` | `/api/projetos/{id}/tarefas/` | Listar / criar tarefas | Sim |
| `GET / PUT / PATCH / DELETE` | `/api/projetos/{id}/tarefas/{tid}/` | CRUD de tarefa | Sim |
| `GET / POST` | `/api/projetos/{id}/tarefas/{tid}/observacoes/` | Listar / criar observações | Sim |
| `PATCH / DELETE` | `/api/projetos/{id}/tarefas/{tid}/observacoes/{oid}/` | Editar / excluir observação | Sim |

---

## Manual do Usuário / Administrador

### Fluxo típico de uso via API

1. **Registrar-se** com `POST /api/auth/registrar/` (username, e-mail, senha, nome, sobrenome e matrícula).
2. **Fazer login** em `POST /api/auth/login/` e guardar os tokens retornados.
3. **Criar um projeto** via `POST /api/projetos/` (o criador vira Líder automaticamente).
4. **Convidar colegas** em `POST /api/projetos/{id}/convites/` com o `username` do colega.
5. O colega **aceita** em `POST /api/convites/{id}/aceitar/`.
6. O líder **cria tarefas** em `POST /api/projetos/{id}/tarefas/` com título, descrição, responsável e prazo.
7. Qualquer membro **atualiza o status** via `PATCH /api/projetos/{id}/tarefas/{tid}/`.
8. Membros **comentam** em `POST /api/projetos/{id}/tarefas/{tid}/observacoes/`.

### Regras de permissão

| Ação | Quem pode |
|---|---|
| Criar / editar / excluir projeto | Líder |
| Remover membro | Líder |
| Enviar convites | Líder |
| Criar / excluir tarefas | Líder |
| Alterar status da tarefa | Qualquer membro |
| Editar título / descrição / prazo | Líder |
| Criar observação | Qualquer membro |
| Editar / excluir observação | Autor da observação ou Líder |

---

## O que funcionou

Autenticação completa: registro, login, logout com blacklist do refresh token e renovação automática do access token. Troca de senha com validação da senha atual.

CRUD de Projetos, Tarefas e Observações funcionando, com controle de papéis Líder/Membro aplicado em todos os endpoints sensíveis.

Sistema de convites: envio, aceitação, recusa e reenvio após recusa. Mudança de status de tarefa gera observação automática no histórico.

Swagger UI e ReDoc ativos. Admin Django com inlines de membros e tarefas. CORS e arquivos estáticos configurados via WhiteNoise.

---

## O que não funcionou

**Esqueci minha senha (reset por e-mail):** o fluxo de recuperação de senha não foi implementado. O endpoint `/api/auth/trocar-senha/` exige autenticação prévia, então um usuário que esqueceu a senha e não consegue entrar perde acesso.

---

> Link do site:
