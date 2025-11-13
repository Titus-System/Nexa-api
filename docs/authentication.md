Aqui está a tradução para o português:

## Visão Geral da Autenticação

O `Flask-JWT-Extended` protege a API Nexa usando "bearer tokens" (tokens de portador). O `Flask-Bcrypt` aplica hash a cada senha armazenada. Usuários podem se registrar, fazer login para receber um JWT e, então, incluí-lo nos cabeçalhos de todos os endpoints protegidos.

### Dependências

  - `Flask-JWT-Extended`
  - `Flask-Bcrypt`
  - `PyJWT`
  - `email-validator`

### Configuração

O arquivo `app/__init__.py` agora inicializa o JWT e o Bcrypt usando valores de `app.config.settings`:

  - `JWT_SECRET_KEY`: segredo usado para assinar os tokens de acesso JWT
  - `JWT_ACCESS_TOKEN_EXPIRES`: tempo de vida do token em segundos (padrão de 24h)

Defina substituições (overrides) no seu arquivo `.env` ao executar fora do ambiente de desenvolvimento.

### Registro

`POST /register`
Cria um novo usuário com uma senha hasheada.

```
{
  "name": "Analista",
  "email": "analista@nexa.io",
  "password": "MudeMe!",
  "role_name": "USER"
}
```

Respostas:

  - `201 Created`: retorna o id, nome e email do novo usuário
  - `400 Bad Request`: falha na validação ou o e-mail já existe

### Login

`POST /login`
Verifica as credenciais e retorna um token de acesso JWT (string) no campo `access_token`.

```
{
  "email": "analista@nexa.io",
  "password": "MudeMe!"
}
```

Exemplo de resposta:

```
{
  "access_token": "<token JWT>",
  "user": {
    "id": 7,
    "name": "Analista",
    "email": "analista@nexa.io"
  }
}
```

Use o token no cabeçalho (header) `Authorization` como `Bearer <token>`.

### Endpoints Protegidos

Rotas como `/tasks`, `/classify-partnumber`, `/classify-batch` e `/upload-pdf` usam um "decorator" customizado `jwt_required_optional`. A função auxiliar (helper) `get_current_user_id()` tenta ler o id do usuário autenticado, recorrendo à conta do sistema (`id = 1`) (fallback) quando nenhum JWT válido é fornecido. Isso garante retrocompatibilidade (backward compatibility) para fluxos existentes que dependiam do usuário do sistema.

Todas as consultas na camada de serviço (service-layer) filtram por `user_id = get_current_user_id()` para manter os dados de cada usuário isolados. Quando a conta de fallback é usada, os resultados pertencem ao usuário do sistema.

### Fluxo Típico

1.  `POST /register`
2.  `POST /login`
3.  Envie o token recebido no cabeçalho de cada requisição:
    `Authorization: Bearer <token>`
4.  Receba apenas os dados restritos (scoped) ao usuário autenticado

Se você omitir o token, suas requisições serão executadas como o usuário do sistema, e assim você operará sobre os dados do usuário padrão.

### Solução de Problemas

  - `401 E-mail ou senha inválidos`: verifique as credenciais
  - `422 Cabeçalho de Autorização Ausente`: inclua o "bearer token" quando exigido; caso contrário, o fallback para o usuário do sistema será usado
  - `Garanta que a JWT_SECRET_KEY seja a mesma em todas as instâncias da aplicação`