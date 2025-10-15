## API Nexa – Comunicação Frontend ↔️ Nexa-api
---

## 1. Visão Geral

Esta API permite que clientes solicitem a classificação de partnumbers de forma assíncrona, utilizando:
- **HTTP REST** para iniciar a tarefa
- **WebSocket (Socket.IO)** para receber progresso e resultado final

---

## 2. HTTP REST

### 2.1. Iniciar Classificação

- **Endpoint:** `/classify-partnumber`
- **Método:** `POST`
- **Content-Type:** `application/json`

#### Corpo da Requisição

```json
{
  "partnumber": "PN-TEST-12345",
  "description": "[opcional] Descrição do produto",
  "manufacturer": "[opcional] Fabricante",
  "supplier": "[opcional] Fornecedor",
  "reclassify": true
}
```

Campos:
- `partnumber` (**obrigatório**): string
- `description`, `manufacturer`, `supplier`: string (opcionais)
- `reclassify`: boolean (opcional, false por padrão)

#### Resposta de Sucesso (`202 Accepted`)

```json
{
  "message": "Seu pedido de classificação foi aceito e está sendo processado...",
  "task_id": "673803c3-1993-49c5-9a5d-febdff5a6200",
  "room_id": "231ac3f7-e31d-43c5-9213-b1919d4db6ff",
  "classifications": [
    {
      "created_at": "2025-10-15T19:08:14.299905Z",
      "updated_at": null,
      "id": 1,
      "partnumber_id": 1,
      "classification_task_id": "fa3c27cb-7148-49c7-ae94-42e459ce9fb9",
      "tipi_id": null,
      "manufacturer_id": null,
      "created_by_user_id": 1,
      "short_description": "Short Description",
      "long_description": "Long and complete description.",
      "status": "ACTIVE",
      "confidence_rate": 0.98
    }
  ]
}
```

### 2.2. Buscar Task

- **Endpoint:** `/tasks`
- **Método:** `GET`

#### Query String Parameters
| Parâmetro          | Tipo   | Obrigatório | Descrição                                            |
| ------------------ | ------ | ----------- | ---------------------------------------------------- |
| `task_id`          | string | Não         | ID da tarefa específica.                             |
| `job_id`           | string | Não         | ID do job ao qual a tarefa pertence.                 |
| `progress_channel` | string | Não         | Canal de progresso associado à tarefa.               |
| `status`           | string | Não         | Status da tarefa (ex: `running`, `done`, `pending`). |
| `user_id`          | string | Não         | ID do usuário responsável pela tarefa.               |

> Todos os parâmetros são opcionais, mas você pode combinar múltiplos filtros em uma única requisição.


#### **Exemplos de Requisição**

1️⃣ Buscar tarefa por `task_id`:

```
GET /tasks?task_id=123
```

2️⃣ Buscar tarefas de um usuário específico com status `running`:

```
GET /tasks?user_id=10&status=running
```

3️⃣ Buscar tarefas por `job_id` e `progress_channel`:

```
GET /tasks?job_id=456&progress_channel=room_abc
```

---

#### **Resposta**

* **Status:** 200 OK
* **Formato:** JSON

```json
{
  "tasks": [
    {
      "task_id": "1",
      "job_id": "456",
      "user_id": "10",
      "status": "running",
      "progress_channel": "room_abc",
      "created_at": "2025-10-15T12:00:00",
      "updated_at": "2025-10-15T12:10:00"
    },
    {
      "task_id": "2",
      "job_id": "456",
      "user_id": "10",
      "status": "running",
      "progress_channel": "room_xyz",
      "created_at": "2025-10-15T12:05:00",
      "updated_at": "2025-10-15T12:15:00"
    }
  ]
}
```

---

## 3. WebSocket (Socket.IO)

### 3.1. Conexão

- **URL:** `ws://localhost:5000`
- Após conectar, o servidor emite:
  ```json
  { "socket_session_id": "<id-da-sessao>" }
  ```

### 3.2. Eventos do Cliente para o Servidor

| Evento       | Payload (JSON)            | Descrição                                                                 |
|--------------|--------------------------|--------------------------------------------------------------------------|
| `join`       | `{ "room_id": "..." }`   | Entra na sala para receber updates da tarefa (obrigatório após o POST)   |
| `ping_event` | qualquer                 | Testa a conexão. O servidor responde com `pong_event`.                   |
| `message`    | string                   | Mensagem de texto simples (ecoada pelo servidor).                        |

### 3.3. Eventos do Servidor para o Cliente

| Evento                         | Payload (JSON)                      | Descrição                                                        |
|---------------------------------|-------------------------------------|-------------------------------------------------------------------|
| `connected`                    | `{ "socket_session_id": "..." }`   | Emissão automática ao conectar.                                   |
| `pong_event`                   | `{ "message": "pong" }`            | Resposta ao `ping_event`.                                        |
| `classification_update_status` | ver abaixo                          | Progresso da tarefa.                                             |
| `classification_finished`      | ver abaixo                          | Resultado final da classificação.                                 |

#### `classification_update_status` - Exemplo de Payload – Progresso

```json
{
  "status": "processing",
  "current": 2,
  "total": 5,
  "message": "Analisando dados..."
}
```

#### `classification_update_status` - Exemplo de Payload - Falha

```json
{
    "status": "failed",
    "message": "Erro ao iniciar o processamento do partnumber.",
}
```

#### `classification_finished` - Exemplo de Payload – Resultado Final

```json
{
  "status": "done",
  "message": "Processamento concluído com sucesso.",
  "partnumber": "PN-TEST-12345",
  "result": {
    "ncm": "123456788",
    "description": "Descrição detalhada do produto",
    "exception": "01",
    "nve": "01",
    "fabricante": "fábrica Nexa",
    "endereco": "av pequim",
    "pais": "China",
    "confidence_score": 0.98
  }
}
```

**Status possíveis:**
- `processing`: tarefa em andamento
- `done`: tarefa concluída com sucesso
- `failed`: erro durante o processamento

---

## 4. Fluxo Resumido

1. Cliente conecta via WebSocket e recebe seu `socket_session_id`.
2. Cliente faz POST para `/classify-partnumber`.
3. Recebe `room_id` e `task_id`.
4. Cliente emite `join` com o `room_id`.
5. Recebe eventos de progresso (`classification_update_status`).
6. Recebe evento final (`classification_finished`).

---

## 5. Observações

- Use sempre bibliotecas compatíveis com Socket.IO.
- O campo `room_id` é obrigatório para receber updates.
- O payload dos eventos segue os modelos Pydantic em `app/schemas/classification_schemas.py`.
- Para exemplos de uso, veja os testes em `tests/test_classification_task.py`.


### 6\. Exemplo de Implementação Completa (Pseudocódigo / TypeScript)

Este exemplo em TypeScript ilustra o fluxo completo do ponto de vista do cliente.

```typescript
import { io } from 'socket.io-client';

const WEBSOCKET_URL = 'ws://localhost:5000';
const API_URL = 'http://localhost:5000/classify-partnumber';

// 1. Iniciar a conexão WebSocket
const socket = io(WEBSOCKET_URL);

// Função principal que orquestra o processo
async function startClassificationProcess(partnumber: string) {
  socket.on('connect', () => {
    console.log(`Conectado ao WebSocket com ID: ${socket.id}`);
    
    // Agora que temos o ID, podemos fazer a chamada HTTP
    initiateClassification(partnumber, socket.id!);
  });
}

// 2. Fazer a chamada HTTP para iniciar a tarefa
async function initiateClassification(partnumber: string, sessionId: string) {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        partnumber: partnumber,
        socket_session_id: sessionId
      })
    });

    if (response.status !== 202) {
      throw new Error('Falha ao iniciar a classificação.');
    }

    const { room_id } = await response.json();
    console.log(`Tarefa iniciada. Inscrevendo-se na sala: ${room_id}`);

    // 3. Inscrever-se na sala para receber atualizações
    socket.emit('join', { room_id: room_id });
    
    // 4. Configurar listeners para os eventos de progresso e finalização
    setupListeners();

  } catch (error) {
    console.error("Erro no processo de classificação:", error);
  }
}

// Função para registrar os listeners de eventos
function setupListeners() {
  socket.on('classification_update_status', (data) => {
    console.log('UPDATE:', data);
    // Lógica para atualizar a UI com o progresso
    // ex: updateProgressBar(data.progress);
  });

  socket.on('classification_finished', (data) => {
    console.log('FINISHED:', data);
    // Lógica para exibir o resultado final
    // ex: displayResult(data.result);

    // Tarefa concluída, podemos desconectar
    socket.disconnect();
  });
}

// Iniciar o processo
startClassificationProcess("PN-TS-TEST-12345");
```