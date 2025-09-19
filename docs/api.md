## **Documentação da API WebSocket – Classificação de Partnumber**

**Versão:** 1.0
**Última Atualização:** 18 de Setembro de 2025

### 1\. Visão Geral

Esta API fornece um mecanismo para solicitar a classificação de *partnumbers* de forma assíncrona. Para evitar longos tempos de espera em requisições HTTP, o sistema utiliza uma combinação de uma chamada REST para iniciar a tarefa e uma conexão WebSocket para comunicar o progresso e o resultado final em tempo real.

O backend é construído com **Flask** e **Flask-SocketIO**, o que significa que os clientes **devem** usar uma biblioteca compatível com o protocolo **Socket.IO** (por exemplo, `socket.io-client` para JavaScript/TypeScript, `python-socketio` para Python) para garantir a compatibilidade.

### 2\. Fluxo de Operação Essencial

O processo de classificação segue 4 passos principais:

1.  **Conexão WebSocket:** O cliente primeiro estabelece uma conexão persistente com o nosso servidor Socket.IO.
2.  **Requisição HTTP:** O cliente envia uma requisição `POST` para o endpoint REST `/classify-partnumber` contendo o *partnumber* a ser classificado.
3.  **Inscrição na Sala:** A API REST responde imediatamente (`202 Accepted`) com um `room_id` único para esta tarefa. O cliente deve, então, usar sua conexão WebSocket para se inscrever nesta sala.
4.  **Recebimento de Atualizações:** O servidor emitirá todos os eventos de progresso e o resultado final da classificação para a sala (`room_id`) específica. O cliente apenas precisa escutar os eventos.

### 3\. Endpoint de Conexão WebSocket

Em ambiente de desenvolvimento, utilize o seguinte endpoint para estabelecer a conexão Socket.IO:
`ws://localhost:5000`

Após a conexão, o servidor emitirá um evento `connected` contendo o ID da sua sessão.

### 4\. API REST – Início da Classificação

Para iniciar uma nova tarefa de classificação, faça uma requisição HTTP.

  * **Endpoint:** `/classify-partnumber`
  * **Método:** `POST`
  * **Content-Type:** `application/json`

#### Corpo da Requisição (Request Body)

```json
{
  "partnumber": "PN-TEST-12345",
  "description": "[opcional] Descrição ou detalhes adicionais do produto",
  "manufacturer": "[opcional] Fabricante do produto",
  "supplier": "[opcional] Fornecedor do produto"
}
```

  * `partnumber` (string, obrigatório): O partnumber a ser classificado.
  * `description` (string, opcional): Uma descrição para auxiliar na classificação.
  * `manufacturer` (string, opcional): Nome do fabricante do produto
  * `supplier` (string, opcional): Nome do fornecedor do produto em questão

#### Resposta de Sucesso (`202 Accepted`)

```json
{
  "message": "Seu pedido de classificação foi aceito...",
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890aalkdsh",
  "room_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

  * `room_id` (string): O ID da sala que você deve usar para escutar as atualizações.

### 5\. API de Eventos WebSocket

#### 5.1. Eventos Emitidos pelo Cliente (Cliente -\> Servidor)

| Evento       | Payload (JSON)            | Descrição                                                                                                                                     |
| :----------- | :------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| **`join`**   | `{ "room_id": "string" }` | **(Obrigatório)**. Após receber o `room_id` da API REST, o cliente **deve** emitir este evento para começar a receber atualizações da tarefa. |
| `ping_event` | (qualquer)                | Evento de teste para verificar a conexão. O servidor responderá com um `pong_event`.                                                          |
| `message`    | `string`                  | Evento padrão do Socket.IO para enviar uma mensagem de texto simples. O servidor responderá com um "Echo".                                    |

#### 5.2. Eventos Emitidos pelo Servidor (Servidor -\> Cliente)

| Evento                         | Payload (JSON)                      | Descrição                                                                                                                         |
| :----------------------------- | :---------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `connected`                    | `{ "socket_session_id": "string" }` | Emitido imediatamente após uma conexão bem-sucedida. O cliente deve armazenar o `socket_session_id` para usar na requisição POST. |
| `pong_event`                   | `{ "message": "pong" }`             | Resposta ao evento `ping_event` do cliente.                                                                                       |
| `classification_update_status` | `objeto`                            | Emitido periodicamente durante o processamento para informar o progresso. A estrutura exata do objeto pode variar.                |
| `classification_finished`      | `objeto`                            | Emitido uma única vez quando a tarefa é concluída, contendo o resultado final da classificação.                                   |

#### Estrutura de Payload (Exemplos)

**Exemplo de Payload para `classification_update_status`:**

```json
{
  "current":"2",
  "total":"5",
  "status": "processing",
  "message": "Analisando dados...",
}
```

**Exemplo de Payload para `classification_finished`:**

```json
{
    "partnumber": "PN-TEST-12345",
    "description": "Descrição detalhada do produto a partir do partnumber",
    "status": "done"
}
```

*(Nota: a estrutura dos payloads de `update` e `finished` são exemplos e devem ser confirmados com a implementação exata do DTO do backend).*

**possíveis `status`:** 
- `processing`: indica que o processamento do pedido está correndo corretamente e deve ser finalizada em breve
- `done`: indica a finalização do processamento e a comunicação da resposta final da aplicação
- `failed`: indica que o processamento falhou e foi interrompido devido a algum erro interno da aplicação

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