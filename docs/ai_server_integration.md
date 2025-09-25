# Integração Nexa API ↔️ Servidor de IA (AI Server)

## Visão Geral

A integração entre a Nexa API e o Servidor de IA utiliza um padrão híbrido de comunicação:
- **HTTP REST** para iniciar o processamento de classificação.
- **Redis Pub/Sub** para acompanhar o progresso e receber o resultado final de forma assíncrona.

Esse modelo visa desacoplamento e comunicação em tempo real entre os sistemas.

---

## 1. Fluxo Completo da Comunicação

### 1.1. Início da Tarefa (HTTP POST)
- A Nexa API recebe uma requisição REST do cliente para classificar um partnumber.
- A Nexa API gera um canal de progresso único (ex: `progress-<uuid>`).
- A Nexa API faz um **POST** para o endpoint do Servidor de IA:

  **Endpoint:**
  ```
  POST {NEXA_AI_SERVER}/process/single_partnumber
  ```

  **Payload:**
  ```json
  {
    "progress_channel": "progress-123e4567-e89b-12d3-a456-426614174000",
    "partnumber": "PN-TEST-12345",
    "description": "[opcional] Descrição do produto",
    "manufacturer": "[opcional] Fabricante",
    "supplier": "[opcional] Fornecedor"
  }
  ```
  **Schema real:**
    ```python
    class AISingleClassificationRequest(BaseModel):
        progress_channel: str
        partnumber: str
        description: Optional[str] = None
        manufacturer: Optional[str] = None
        supplier: Optional[str] = None
    ```

- O Servidor de IA responde imediatamente com:
  ```json
  {
    "job_id": "abc-123-xyz"
  }
  ```

### 1.2. Progresso da Tarefa (Redis Pub/Sub)
- O Servidor de IA publica mensagens de progresso no canal Redis informado (`progress_channel`).
- A Nexa API está inscrita nesse canal e retransmite cada atualização para o frontend via WebSocket.

  **Exemplo de mensagem de progresso:**
  ```json
  {
    "status": "processing",
    "job_id": "abc-123-xyz",
    "progress": {
      "current": 2,
      "total": 5,
      "message": "Analisando dados..."
    }
  }
  ```

### 1.3. Falha na conslusão da tarefa (Redis Pub/Sub)
- O Servidor de IA publica mensagens de falha no canal Redis informado (`progress_channel`).

    ```json
    {
    "status": "failed",
    "job_id": "abc-123-xyz",
    "error": "Descrição do erro"
    }
    ```

### 1.4. Finalização da Tarefa
- Ao concluir, o Servidor de IA publica no mesmo canal:
  ```json
  {
    "status": "done",
    "job_id": "abc-123-xyz",
    "result": {
      "ncm": "12345678",
      "description": "Descrição detalhada",
      "exception": "01",
      "nve": "01",
      "fabricante": "fábrica Nexa",
      "endereco": "av pequim",
      "pais": "China",
      "confidence_score": 0.98
    }
  }
  ```

- A Nexa API intercepta essa mensagem, publica o resultado final no canal Redis principal (`task_results`) e encerra a sala WebSocket do usuário.

---

## 2. Especificação dos Endpoints e Mensagens

### 2.1. Endpoint de Início
- **URL:** `{NEXA_AI_SERVER}/process/single_partnumber`
- **Método:** `POST`
- **Content-Type:** `application/json`
- **Body:**
  - `progress_channel` (string, obrigatório): nome do canal Redis para updates.
  - `partnumber` (string, obrigatório)
  - `description`, `manufacturer`, `supplier` (opcionais)

### 2.2. Mensagens Redis (do AI Server para Nexa API)
- **Canal:** `progress-<uuid>` (dinâmico)
- **Formato:**
  - Progresso:
    ```json
    { "status": "processing", "progress": { "current": 1, "total": 5, "message": "..." } }
    ```
  - Falha:
    ```json
    { "status": "failed", "error": "Mensagem de erro" }
    ```
  - Finalização:
    ```json
    { "status": "done", "result": { ...campos do resultado... } }
    ```

### 2.3. Mensagem Redis (da Nexa API para o frontend)
- **Canal:** `task_results`
- **Formato:**
  ```json
  {
    "status": "done",
    "message": "Processamento concluído com sucesso.",
    "partnumber": "PN-TEST-12345",
    "result": { ... },
    "room_id": "..."
  }
  ```

---

## 3. Observações Importantes

- O Servidor de IA **nunca** se inscreve em canais Redis, apenas publica.
- O canal de progresso é **único por tarefa** e informado pela Nexa API.
- O resultado final deve conter todos os campos esperados pelo frontend (ver schemas Pydantic em `app/schemas/classification_schemas.py`).
- Mensagens de erro devem ser publicadas com `status: failed` e campo `error`.
- O fluxo é tolerante a falhas: se o job não iniciar, a Nexa API notifica o frontend imediatamente.

---

## 4. Exemplo de Sequência

1. Nexa API gera canal: `progress-123`.
2. Nexa API faz POST para o AI Server com o canal e dados.
3. AI Server publica progresso em `progress-123`.
4. Ao finalizar, AI Server publica resultado em `progress-123`.
5. Nexa API publica resultado final em `task_results`.
6. Frontend recebe evento via WebSocket.

---
