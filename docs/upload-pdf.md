# 📄 Endpoint: Upload de Pedido e Início da Classificação em Lote

## 🧠 Visão Geral

Esta rota permite o envio de um **arquivo PDF contendo um pedido de compra**, realiza a **extração automática dos Part Numbers (PNs)** e **inicia um processo de classificação em lote** desses códigos.

A requisição é feita via `multipart/form-data`, e o arquivo é processado **diretamente em memória** — sem ser salvo em disco.
Após a extração, o backend cria uma tarefa de classificação (`task_id`) e um identificador de sala (`room_id`) para acompanhar o processamento em tempo real (por exemplo, via WebSocket).

---

## 🔗 URL Padrão

```
POST /upload-pdf
```

### 📦 Tipo de Requisição

`multipart/form-data`

---

## 📥 O que a rota espera receber

A rota espera **um arquivo PDF** e **alguns campos opcionais** de controle de processamento.

| Campo        | Tipo                         | Obrigatório | Descrição                                                                                       |
| ------------ | ---------------------------- | ----------- | ----------------------------------------------------------------------------------------------- |
| `pedido`     | `File (.pdf)`                | ✅           | Arquivo PDF contendo o pedido de compra.                                                        |
| `user_id`    | `integer`                    | ❌           | ID do usuário que enviou o pedido. Padrão: `1`.                                                 |
| `reclassify` | `boolean` (`true` / `false`) | ❌           | Indica se os PNs devem ser reclassificados, mesmo que já existam no histórico. Padrão: `false`. |

---

### 🧩 Exemplo de envio no Postman / Insomnia

* Método: `POST`
* URL: `http://localhost:5000/upload-pdf`
* Body → `form-data`

  * **Key:** `pedido` → Type: `File` → Value: `pedido_cliente.pdf`
  * **Key:** `user_id` → Type: `Text` → Value: `12`
  * **Key:** `reclassify` → Type: `Text` → Value: `true`

---

## ⚙️ Etapas de Processamento Interno

1. **Validação do arquivo:**
   Verifica se o campo `pedido` existe, se o nome não está vazio e se o formato é `.pdf`.

2. **Leitura em memória:**
   O arquivo é lido diretamente em memória (`file.read()`), sem criação de arquivos temporários.

3. **Extração de Part Numbers:**
   O método `extract_part_numbers(pdf_bytes)` é chamado e:

   * Abre o PDF com `pdfplumber`;
   * Extrai o texto de todas as páginas;
   * Identifica Part Numbers usando expressões regulares (ex: `PN:XXXXXX` ou códigos alfanuméricos longos);
   * Remove duplicatas e retorna uma lista única e ordenada.

4. **Criação da tarefa de classificação:**
   Gera um `room_id` (UUID) e cria um objeto `StartBatchClassificationSchema` com:

   ```python
   {
     "partnumbers": [...],
     "room_id": "...",
     "reclassify": false,
     "user_id": 1
   }
   ```

   Esse schema é passado para o `ClassificationService.start_batch_classification(schema)`.

5. **Retorno ao cliente:**
   O servidor responde imediatamente com `HTTP 202`, indicando que o processamento foi aceito e será executado de forma assíncrona.

---

## 📤 Respostas (Saída)

### ✅ Sucesso (`HTTP 202`)

```json
{
  "message": "PDF recebido e processado com sucesso! Partnumbers extraídos estão sendo classificados.",
  "task_id": "43d0e8a1-1a8c-4a8d-9f0f-623ba203e64d",
  "room_id": "9df6c237-23a3-4df5-a912-b5dc12e8ad80",
  "classifications": [
    {...},
  ],
  "partnumbers": ["LM358N", "74HC595", "BC337"],
  "total_partnumbers": 3
}
```

| Campo               | Tipo            | Descrição                                                       |
| ------------------- | --------------- | --------------------------------------------------------------- |
| `message`           | `string`        | Mensagem de sucesso.                                            |
| `task_id`           | `string (UUID)` | Identificador único da tarefa de classificação.                 |
| `room_id`           | `string (UUID)` | ID da “sala” associada à tarefa (para WebSocket, se aplicável). |
| `classifications`   | `array`         | Lista com classificações iniciais (caso disponíveis).           |
| `partnumbers`       | `array`         | Lista dos PNs extraídos do PDF.                                 |
| `total_partnumbers` | `integer`       | Quantidade total de Part Numbers encontrados.                   |

---

### ⚠️ Erros Possíveis

| Código | Causa                                                  | Exemplo de Retorno                                            |
| ------ | ------------------------------------------------------ | ------------------------------------------------------------- |
| `400`  | Nenhum arquivo enviado, nome vazio ou formato inválido | `{ "message": "Formato inválido, apenas PDFs são aceitos." }` |
| `500`  | Falha no processamento, extração ou classificação      | `{ "error": "Erro interno: falha ao ler PDF." }`              |

---

## 🧾 Exemplo Completo

### **Requisição**

`POST /upload-pdf`
Body (`multipart/form-data`):

| Key          | Type | Value                    |
| ------------ | ---- | ------------------------ |
| `pedido`     | File | `pedido_cliente_123.pdf` |
| `user_id`    | Text | `7`                      |
| `reclassify` | Text | `false`                  |

### **Resposta**

```json
{
  "message": "PDF recebido e processado com sucesso! Partnumbers extraídos estão sendo classificados.",
  "task_id": "e93847a5-54be-4d9d-8c87-2456dba65a56",
  "room_id": "b0de7c3f-d729-49b0-9e4b-cab2c4c6164e",
  "partnumbers": ["PN:74HC595", "LM358N", "12.237"],
  "total_partnumbers": 3
}
```

---

## 🧩 Resumo Técnico

| Item                       | Descrição                                                  |
| -------------------------- | ---------------------------------------------------------- |
| **Framework**              | Flask + Flask-RESTful                                      |
| **Injeção de dependência** | `dependency_injector` (`Container.classification_service`) |
| **Extração PDF**           | `pdfplumber`                                               |
| **Leitura de arquivo**     | Em memória (`file.read()`)                                 |
| **Validação de schema**    | `pydantic` (`StartBatchClassificationSchema`)              |
| **Tipo de processamento**  | Assíncrono (retorna 202 Accepted)                          |

---

## 💡 Dica para o Front-end

Após o envio do PDF:

* Use o `task_id` ou `room_id` retornado para consultar o progresso da classificação via API ou WebSocket.
* Mostre o total de PNs encontrados e o status de “processando” até a classificação final estar disponível.